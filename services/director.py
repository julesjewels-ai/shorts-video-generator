from google import genai
from google.genai import types
from ..core.interfaces import IDirector
from ..core.models import VideoPlan
from ..config import Config
from ..utils.prompt_loader import PromptLoader
from ..utils.logger import setup_logger, save_state

logger = setup_logger()

class DirectorService(IDirector):
    def __init__(self, client: genai.Client):
        self.client = client
        
        # Load optional outfit prompts
        self.leader_outfit = PromptLoader.load_optional("leader_outfit.txt")
        self.follower_outfit = PromptLoader.load_optional("follower_outfit.txt")
        
        # Load optional setting prompt
        self.setting = PromptLoader.load_optional("setting.txt")
        
        # Build dynamic instructions
        outfit_instructions = self._build_outfit_instructions()
        setting_instructions = self._build_setting_instructions()
        
        # Load and format system instruction with dynamic instructions
        system_template = PromptLoader.load("director_system.txt")
        self.system_instruction = system_template.format(
            outfit_instructions=outfit_instructions,
            setting_instructions=setting_instructions
        )
        
        logger.debug(f"DirectorService initialized with system instruction ({len(self.system_instruction)} chars)")
        logger.debug(f"Leader outfit: {'defined' if self.leader_outfit else 'AI decides'}")
        logger.debug(f"Follower outfit: {'defined' if self.follower_outfit else 'AI decides'}")
        logger.debug(f"Setting: {'defined' if self.setting else 'AI decides'}")

    def _build_outfit_instructions(self) -> str:
        """Build dynamic outfit instructions based on which files are defined."""
        if self.leader_outfit and self.follower_outfit:
            return (
                f"Use these EXACT character descriptions:\n"
                f"- Leader: {self.leader_outfit}\n"
                f"- Follower: {self.follower_outfit}"
            )
        elif self.leader_outfit:
            return (
                f"Use this EXACT description for the leader:\n"
                f"- Leader: {self.leader_outfit}\n"
                f"Design a matching, complementary outfit for the follower."
            )
        elif self.follower_outfit:
            return (
                f"Use this EXACT description for the follower:\n"
                f"- Follower: {self.follower_outfit}\n"
                f"Design a matching, complementary outfit for the leader."
            )
        else:
            return "You have full creative freedom for both character outfits. Design elegant, cinematic outfits that match the dance style."

    def _build_setting_instructions(self) -> str:
        """Build dynamic setting instructions based on whether a setting file is defined."""
        if self.setting:
            return (
                f"Use this EXACT setting/scene description:\n"
                f"- Setting: {self.setting}\n"
                f"Ensure all scenes take place in this environment."
            )
        else:
            return "You have full creative freedom for the setting/scene. Design an elegant, cinematic environment that matches the dance style (e.g., ballroom, rooftop terrace, Spanish plaza)."

    def generate_plan(self, user_input: str) -> VideoPlan:
        print("🎬 Director is thinking (High Reasoning Mode)...")
        
        logger.info(f"generate_plan called with input length: {len(user_input)} chars")
        logger.info(f"Using model: {Config.MODEL_NAME_TEXT}")
        logger.debug(f"API version: {Config.GEMINI_VERSION}")
        
        # Build configuration based on model capabilities
        gen_config_args = {
            "response_mime_type": "application/json",
            "response_json_schema": VideoPlan.model_json_schema(),
        }
        
        logger.debug(f"Base config: response_mime_type=application/json")
        logger.debug(f"JSON schema keys: {list(VideoPlan.model_json_schema().keys())}")

        # Add thinking config only for supported models (Gemini 3+)
        if "gemini-3" in Config.MODEL_NAME_TEXT:
            logger.info("Enabling Thinking Mode (High Reasoning) for Gemini 3...")
            gen_config_args["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
            gen_config_args["temperature"] = 1.0  # Default required for Gemini 3 reasoning
            gen_config_args["system_instruction"] = self.system_instruction
            logger.debug("Added thinking_config, temperature=1.0, and system_instruction to config")
        else:
            logger.info(f"Model {Config.MODEL_NAME_TEXT}: Thinking Mode not available")
            logger.info("Adding system_instruction to config for non-Gemini-3 models")
            # For Gemini 2.5 Flash with v1beta, system_instruction should work in config
            gen_config_args["system_instruction"] = self.system_instruction
            logger.debug("Added system_instruction to config (v1beta supports this)")

        # Log final configuration
        config_summary = {
            "response_mime_type": gen_config_args.get("response_mime_type"),
            "has_json_schema": "response_json_schema" in gen_config_args,
            "has_thinking_config": "thinking_config" in gen_config_args,
            "temperature": gen_config_args.get("temperature"),
            "has_system_instruction": "system_instruction" in gen_config_args,
        }
        logger.info(f"Final config summary: {config_summary}")
        
        save_state("director_config", {
            "model": Config.MODEL_NAME_TEXT,
            "api_version": Config.GEMINI_VERSION,
            "config_summary": config_summary,
            "user_input_length": len(user_input),
            "system_instruction_length": len(self.system_instruction)
        }, logger)

        config = types.GenerateContentConfig(**gen_config_args)
        
        try:
            logger.info("Calling Gemini API for plan generation...")
            logger.debug(f"Contents length: {len(user_input)} chars")
            
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME_TEXT,
                contents=user_input, 
                config=config,
            )
            
            logger.info("API response received successfully")
            logger.debug(f"Response text length: {len(response.text) if response.text else 0}")
            logger.debug(f"Response text preview: {response.text[:500] if response.text else 'None'}...")
            
            # Save raw response
            save_state("director_response_raw", {
                "response_text": response.text,
                "response_length": len(response.text) if response.text else 0
            }, logger)
            
            # Validate and parse
            logger.info("Parsing response JSON into VideoPlan...")
            plan = VideoPlan.model_validate_json(response.text)
            
            logger.info(f"Plan parsed successfully: {plan.title}")
            logger.debug(f"Plan details - scenes: {len(plan.scenes)}, tags: {plan.backend_tags}")
            
            # Save parsed plan
            save_state("director_plan_parsed", {
                "title": plan.title,
                "description": plan.description,
                "scenes_count": len(plan.scenes),
                "scenes": [s.model_dump() for s in plan.scenes],
                "backend_tags": plan.backend_tags,
                "setting_desc": plan.setting_desc,
                "character_leader_desc": plan.character_leader_desc,
                "character_follower_desc": plan.character_follower_desc
            }, logger)
            
            print(f"✅ Plan Generated: {plan.title}")
            return plan

        except Exception as e:
            logger.error(f"Error generating plan: {e}", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
            
            # Save error state
            save_state("director_error", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "model": Config.MODEL_NAME_TEXT,
                "api_version": Config.GEMINI_VERSION
            }, logger)
            
            print(f"❌ Error generating plan: {e}")
            raise
