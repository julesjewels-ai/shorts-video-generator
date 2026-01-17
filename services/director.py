from typing import Dict, Any
from typing import Generator
from google import genai
from google.genai import types
from ..core.interfaces import IDirector
from ..core.models import VideoPlan
from ..core.stream_models import StreamChunk, StreamChunkType
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
        if not self.leader_outfit and not self.follower_outfit:
            return "You have full creative freedom for both character outfits. Design elegant, cinematic outfits that match the dance style."

        instructions = []
        if self.leader_outfit:
            instructions.append(f"Use this EXACT description for the leader:\n- Leader: {self.leader_outfit}")
        else:
            instructions.append("Design a matching, complementary outfit for the leader.")

        if self.follower_outfit:
            instructions.append(f"Use this EXACT description for the follower:\n- Follower: {self.follower_outfit}")
        else:
            instructions.append("Design a matching, complementary outfit for the follower.")

        return "\n".join(instructions)

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

    def _build_generation_config(self) -> Dict[str, Any]:
        """Builds the configuration dictionary for the Gemini API call."""
        config = {
            "response_mime_type": "application/json",
            "response_json_schema": VideoPlan.model_json_schema(),
        }

        # Add thinking config only for supported models (Gemini 3+)
        if "gemini-3" in Config.MODEL_NAME_TEXT:
            logger.info("Enabling Thinking Mode (High Reasoning) for Gemini 3...")
            config["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
            config["temperature"] = 1.0  # Default required for Gemini 3 reasoning
            config["system_instruction"] = self.system_instruction
        else:
            logger.info(f"Model {Config.MODEL_NAME_TEXT}: Thinking Mode not available")
            # For Gemini 2.5 Flash with v1beta, system_instruction should work in config
            config["system_instruction"] = self.system_instruction

        return config

    def _log_and_save_config(self, config_args: Dict[str, Any], user_input_len: int):
        """Logs and saves the generation configuration."""
        config_summary = {
            "response_mime_type": config_args.get("response_mime_type"),
            "has_json_schema": "response_json_schema" in config_args,
            "has_thinking_config": "thinking_config" in config_args,
            "temperature": config_args.get("temperature"),
            "has_system_instruction": "system_instruction" in config_args,
        }
        logger.info(f"Final config summary: {config_summary}")
        
        save_state("director_config", {
            "model": Config.MODEL_NAME_TEXT,
            "api_version": Config.GEMINI_VERSION,
            "config_summary": config_summary,
            "user_input_length": user_input_len,
            "system_instruction_length": len(self.system_instruction)
        }, logger)

    def _parse_and_save_plan(self, response_text: str) -> VideoPlan:
        """Parses the API response and saves the plan."""
        # Save raw response
        save_state("director_response_raw", {
            "response_text": response_text,
            "response_length": len(response_text) if response_text else 0
        }, logger)

        # Validate and parse
        logger.info("Parsing response JSON into VideoPlan...")
        plan = VideoPlan.model_validate_json(response_text)

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

        return plan

    def generate_plan(self, user_input: str) -> VideoPlan:
        print("🎬 Director is thinking (High Reasoning Mode)...")

        logger.info(f"generate_plan called with input length: {len(user_input)} chars")
        logger.info(f"Using model: {Config.MODEL_NAME_TEXT}")

        # 1. Build Config
        gen_config_args = self._build_generation_config()
        self._log_and_save_config(gen_config_args, len(user_input))

        config = types.GenerateContentConfig(**gen_config_args)
        
        try:
            logger.info("Calling Gemini API for plan generation...")
            
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME_TEXT,
                contents=user_input, 
                config=config,
            )
            
            logger.info("API response received successfully")
            
            # 2. Parse and Save Plan
            plan = self._parse_and_save_plan(response.text)
            
            print(f"✅ Plan Generated: {plan.title}")
            return plan

        except Exception as e:
            logger.error(f"Error generating plan: {e}", exc_info=True)
            
            # Save error state
            save_state("director_error", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "model": Config.MODEL_NAME_TEXT,
                "api_version": Config.GEMINI_VERSION
            }, logger)
            
            print(f"❌ Error generating plan: {e}")
            raise

    def generate_plan_stream(self, user_input: str) -> Generator[StreamChunk, None, None]:
        """Generates a video plan via Gemini API with streaming."""
        logger.info(f"generate_plan_stream called with input length: {len(user_input)} chars")

        # 1. Build Config
        gen_config_args = self._build_generation_config()
        self._log_and_save_config(gen_config_args, len(user_input))

        config = types.GenerateContentConfig(**gen_config_args)

        try:
            logger.info("Calling Gemini API for streaming plan generation...")

            # Use streaming API
            response_stream = self.client.models.generate_content_stream(
                model=Config.MODEL_NAME_TEXT,
                contents=user_input,
                config=config,
            )

            accumulated_text = ""

            for chunk in response_stream:
                if chunk.text:
                    accumulated_text += chunk.text
                    yield StreamChunk(type=StreamChunkType.TOKEN, content=chunk.text)

            logger.info("Stream complete. Parsing accumulated text...")

            # 2. Parse and Save Plan
            plan = self._parse_and_save_plan(accumulated_text)

            yield StreamChunk(type=StreamChunkType.PLAN, content=plan.model_dump())

        except Exception as e:
            logger.error(f"Error during streaming generation: {e}", exc_info=True)
             # Save error state
            save_state("director_stream_error", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "model": Config.MODEL_NAME_TEXT,
            }, logger)
            yield StreamChunk(type=StreamChunkType.ERROR, content=str(e))
            raise
