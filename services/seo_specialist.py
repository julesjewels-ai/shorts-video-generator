import csv
import io
import json
import os
from typing import Tuple

from google import genai
from google.genai import types

from ..config import Config
from ..core.models import VideoPlan, MetadataAlternatives, MetadataConfig
from ..utils.prompt_loader import PromptLoader
from ..utils.logger import setup_logger, save_state

logger = setup_logger()


class SEOSpecialistService:
    """
    SEO Specialist that empathises with the target audience and creates
    emotionally-resonant metadata strategies.
    """

    def __init__(self, client: genai.Client):
        self.client = client
        self.system_template = PromptLoader.load("seo_specialist_system.txt")
        logger.debug(f"SEOSpecialistService initialized with system template ({len(self.system_template)} chars)")

    def load_config(self) -> MetadataConfig:
        """Load metadata configuration from prompts/metadata_config.txt"""
        config_path = os.path.join(Config.PROMPTS_DIR, "metadata_config.txt")
        
        language = "English"
        target_keywords = None
        spreadsheet_content = None
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    
                    if line.startswith('language:'):
                        value = line.split(':', 1)[1].strip()
                        if value:
                            language = value
                    
                    elif line.startswith('target_keywords:'):
                        value = line.split(':', 1)[1].strip()
                        if value:
                            target_keywords = [kw.strip() for kw in value.split(',') if kw.strip()]
                    
                    elif line.startswith('spreadsheet_path:'):
                        value = line.split(':', 1)[1].strip()
                        if value and os.path.exists(value):
                            spreadsheet_content = self._load_spreadsheet(value)
                        elif value:
                            # Try relative to prompts directory
                            full_path = os.path.join(Config.PROMPTS_DIR, value)
                            if os.path.exists(full_path):
                                spreadsheet_content = self._load_spreadsheet(full_path)
        
        config = MetadataConfig(
            language=language,
            target_keywords=target_keywords,
            spreadsheet_content=spreadsheet_content
        )
        
        logger.info(f"Loaded metadata config: language={language}, keywords={target_keywords is not None}, spreadsheet={spreadsheet_content is not None}")
        return config

    def _load_spreadsheet(self, path: str) -> str:
        """Load spreadsheet content as raw string."""
        logger.info(f"Loading spreadsheet from: {path}")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Loaded spreadsheet content ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Failed to load spreadsheet: {e}")
            return None

    def _build_system_instruction(self, config: MetadataConfig, plan: VideoPlan) -> str:
        """Build the system instruction with dynamic content."""
        
        # Language instruction
        if config.language.lower() != "english":
            language_instruction = f"IMPORTANT: Generate ALL metadata (title, description, tags) in {config.language}."
        else:
            language_instruction = "Generate metadata in English."
        
        # Audience instruction from the video plan
        audience_instruction = f"""
VIDEO CONTEXT:
- Title concept: {plan.title}
- Description concept: {plan.description}
- Setting: {plan.setting_desc}
- Characters: {plan.character_leader_desc} and {plan.character_follower_desc}
"""
        
        # Keywords instruction
        if config.target_keywords:
            keywords_instruction = f"MUST incorporate these target keywords: {', '.join(config.target_keywords)}"
        else:
            keywords_instruction = "Use your SEO expertise to identify the best keywords for discoverability."
        
        # Research instruction
        if config.spreadsheet_content:
            research_instruction = f"""
SEO RESEARCH DATA (use this to inform your strategy):
```
{config.spreadsheet_content}
```
Analyze this data to understand what works for this audience and competitors.
"""
        else:
            research_instruction = "No additional SEO research data provided. Use general best practices."
        
        return self.system_template.format(
            language_instruction=language_instruction,
            audience_instruction=audience_instruction,
            keywords_instruction=keywords_instruction,
            research_instruction=research_instruction
        )

    def generate_alternatives(self, plan: VideoPlan, config: MetadataConfig) -> MetadataAlternatives:
        """Generate 3 metadata alternatives using emotional/strategic approach."""
        print("🎯 SEO Specialist is crafting metadata strategies...")
        
        logger.info("Generating metadata alternatives")
        logger.debug(f"Language: {config.language}, Keywords: {config.target_keywords}")
        
        system_instruction = self._build_system_instruction(config, plan)
        logger.debug(f"System instruction built ({len(system_instruction)} chars)")
        
        # Build configuration
        gen_config_args = {
            "response_mime_type": "application/json",
            "response_json_schema": MetadataAlternatives.model_json_schema(),
            "system_instruction": system_instruction,
        }
        
        # Add thinking config for Gemini 3+ models
        if "gemini-3" in Config.MODEL_NAME_TEXT:
            logger.info("Enabling Thinking Mode for metadata generation...")
            gen_config_args["thinking_config"] = types.ThinkingConfig(include_thoughts=True)
            gen_config_args["temperature"] = 1.0
        
        config_obj = types.GenerateContentConfig(**gen_config_args)
        
        # User prompt
        user_prompt = f"""
Create 3 emotionally-resonant metadata alternatives for this dance video:

Video Title (from director): {plan.title}
Video Description (from director): {plan.description}
Current Tags: {', '.join(plan.backend_tags)}

Generate alternatives that will connect deeply with the target audience.
"""
        
        save_state("seo_specialist_request", {
            "language": config.language,
            "has_keywords": config.target_keywords is not None,
            "has_spreadsheet": config.spreadsheet_content is not None,
            "plan_title": plan.title
        }, logger)
        
        try:
            logger.info("Calling Gemini API for metadata alternatives...")
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME_TEXT,
                contents=user_prompt,
                config=config_obj,
            )
            
            logger.info("API response received")
            logger.debug(f"Response text: {response.text[:500] if response.text else 'None'}...")
            
            # Parse response
            alternatives = MetadataAlternatives.model_validate_json(response.text)
            
            logger.info(f"Metadata alternatives generated. Recommended: Option {alternatives.recommended}")
            
            save_state("seo_specialist_response", {
                "recommended": alternatives.recommended,
                "reasoning": alternatives.reasoning,
                "option_1_title": alternatives.option_1.title,
                "option_2_title": alternatives.option_2.title,
                "option_3_title": alternatives.option_3.title,
            }, logger)
            
            print(f"✅ Generated 3 metadata alternatives (Recommended: Option {alternatives.recommended})")
            return alternatives
            
        except Exception as e:
            logger.error(f"Error generating metadata alternatives: {e}", exc_info=True)
            save_state("seo_specialist_error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, logger)
            raise

    def save_metadata(self, alternatives: MetadataAlternatives, output_dir: str) -> Tuple[str, str]:
        """Save metadata as both JSON and CSV."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save JSON
        json_path = os.path.join(output_dir, "metadata_options.json")
        json_data = alternatives.model_dump()
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved metadata JSON to {json_path}")
        
        # Save CSV
        csv_path = os.path.join(output_dir, "metadata_options.csv")
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Option', 'Title', 'Description', 'Tags', 'Emotional Hook', 'Text Hook', 'Text Overlay', 'Recommended'])
            
            for i, option in enumerate([alternatives.option_1, alternatives.option_2, alternatives.option_3], 1):
                recommended_mark = '✓' if i == alternatives.recommended else ''
                writer.writerow([
                    i,
                    option.title,
                    option.description,
                    ', '.join(option.tags),
                    option.emotional_hook,
                    option.text_hook,
                    ' | '.join(option.text_overlay),
                    recommended_mark
                ])
            
            # Add reasoning row
            writer.writerow([])
            writer.writerow(['Reasoning:', alternatives.reasoning])
        
        logger.info(f"Saved metadata CSV to {csv_path}")
        
        print(f"📄 Metadata saved to:")
        print(f"   - JSON: {json_path}")
        print(f"   - CSV:  {csv_path}")
        
        return json_path, csv_path
