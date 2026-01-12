import os
import base64
from typing import Dict, List, Any
from google import genai
from google.genai import types
from ..core.interfaces import ICinematographer
from ..core.models import VideoPlan
from ..config import Config
from ..utils.prompt_loader import PromptLoader
from ..utils.logger import setup_logger, save_state

logger = setup_logger()

class CinematographerService(ICinematographer):
    def __init__(self, client: genai.Client):
        self.client = client
        self.output_dir = Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load multiple reference pose images for batch iteration
        self.reference_poses = PromptLoader.load_multiple_images("reference_pose")
        
        # Fall back to single reference pose if no numbered files found
        if not self.reference_poses:
            single_pose = PromptLoader.load_optional_image("reference_pose.png")
            if not single_pose:
                single_pose = PromptLoader.load_optional_image("reference_pose.jpg")
            if single_pose:
                self.reference_poses = [single_pose]
        
        logger.debug(f"CinematographerService initialized with output_dir: {self.output_dir}")
        logger.info(f"Loaded {len(self.reference_poses)} reference pose(s)")
    
    def _build_variety_instruction(self, variety: int) -> str:
        """Build scene variation instructions based on variety level (0-10)."""
        if variety == 0:
            return (
                "Keep the background and scene elements EXACTLY the same. "
                "Only the dancers' poses should change."
            )
        elif variety <= 3:
            return (
                "Keep the background very similar with only minor variations. "
                "Subtle lighting shifts or tiny element changes are allowed, but the scene "
                "should feel nearly identical."
            )
        elif variety <= 6:
            return (
                "Moderate background variation is allowed. You may: \n"
                "- Shift lighting or time of day slightly\n"
                "- Add or remove minor objects\n"
                "- Include 1-2 people or small animals in the distant background\n"
                "Keep the overall composition and location recognizable."
            )
        elif variety <= 9:
            return (
                "Significant background variation is encouraged. You may: \n"
                "- Change time of day noticeably\n"
                "- Alter weather conditions\n"
                "- Add background characters or animals\n"
                "- Transform environmental details substantially\n"
                "Maintain the overall style and vibe."
            )
        else:  # variety == 10
            return (
                "Dramatic scene variation is desired. You may: \n"
                "- Make major changes to setting elements\n"
                "- Shift between different times of day dramatically\n"
                "- Change weather significantly\n"
                "- Add crowds, multiple animals, or busy environments\n"
                "- Transform the scene while preserving the core style and aesthetic\n"
                "Be creative with the environment!"
            )

    def _save_image(self, part, filename):
        """Extracts and saves image from response part."""
        logger.info(f"Attempting to save {filename}...")
        
        if not part.inline_data:
            logger.warning(f"No inline_data found for {filename}.")
            return None

        try:
            data = part.inline_data.data
            image_data = data if isinstance(data, bytes) else base64.b64decode(data)

            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(image_data)
            
            logger.info(f"Saved: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving {filename}: {e}", exc_info=True)
            raise

    def _generate_keyframe_a(self, plan: VideoPlan, reference_pose_index: int) -> Any:
        """Generates the master Keyframe A."""
        logger.info("--- Generating Keyframe A (Master) ---")
        prompt_a = PromptLoader.load_formatted(
            "cinematographer_master.txt",
            setting_desc=plan.setting_desc,
            character_leader_desc=plan.character_leader_desc,
            character_follower_desc=plan.character_follower_desc,
            action=plan.scenes[0].start_pose_description
        )

        contents = [prompt_a]
        if self.reference_poses:
            pose_idx = reference_pose_index % len(self.reference_poses)
            image_bytes, mime_type = self.reference_poses[pose_idx]

            ref_instruction = (
                "\n\nIMPORTANT: Use the attached reference image as a guide for:\n"
                "- The FRAMING and COMPOSITION (shot type, camera angle, how much of the frame the dancers occupy)\n"
                "- The position and pose of the dancers\n"
                "- The body positions and spatial arrangement\n"
                "Apply the character descriptions and setting from above while maintaining the reference image's framing and pose structure."
            )
            contents = [prompt_a + ref_instruction, types.Part.from_bytes(data=image_bytes, mime_type=mime_type)]
            logger.info(f"   Using reference pose {pose_idx + 1}/{len(self.reference_poses)}")

        save_state("cinematographer_keyframe_a_prompt", {
            "prompt": prompt_a,
            "prompt_length": len(prompt_a),
            "has_reference_pose": len(self.reference_poses) > 0,
            "reference_pose_index": reference_pose_index if self.reference_poses else None
        }, logger)

        print("   Generating Keyframe A (Master)...")
        logger.info(f"Calling Gemini API for Keyframe A (model: {Config.MODEL_NAME_IMAGE})")
        return self.client.models.generate_content(
            model=Config.MODEL_NAME_IMAGE,
            contents=contents,
            config=types.GenerateContentConfig(image_config=types.ImageConfig(aspect_ratio="9:16"))
        )

    def _generate_subsequent_keyframe(self, history: List[types.Content], prompt: str, keyframe_name: str) -> Any:
        """Generates a keyframe (B, C, D) based on conversation history."""
        logger.info(f"--- Generating {keyframe_name} (via Editing) ---")
        history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
        
        save_state(f"cinematographer_{keyframe_name.lower().replace(' ', '_')}_prompt", {
            "prompt": prompt,
            "prompt_length": len(prompt)
        }, logger)
        
        print(f"   Generating {keyframe_name} (via Editing)...")
        logger.info(f"Calling Gemini API for {keyframe_name}")
        response = self.client.models.generate_content(model=Config.MODEL_NAME_IMAGE, contents=history)
        return response

    def generate_assets(self, plan: VideoPlan, output_dir: str = None, scene_variety: int = None, reference_pose_index: int = 0) -> Dict[str, str]:
        logger.info(f"Cinematographer: Starting asset generation")
        
        original_output_dir = self.output_dir
        self.output_dir = output_dir if output_dir else self.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        effective_variety = scene_variety if scene_variety is not None else Config.SCENE_VARIETY
        variety_instruction = self._build_variety_instruction(effective_variety)
        
        save_state("cinematographer_start", {
            "target_dir": self.output_dir,
            "plan_title": plan.title,
            "scenes_count": len(plan.scenes),
            "scene_variety": effective_variety
        }, logger)
        
        try:
            assets = {}
            
            # 1. Keyframe A
            response_a = self._generate_keyframe_a(plan, reference_pose_index)
            part_a = [p for p in response_a.parts if p.inline_data][0]
            assets['A'] = self._save_image(part_a, "keyframe_A.png")
            
            save_state("cinematographer_keyframe_a_complete", {
                "path": assets['A'],
                "status": "success"
            }, logger)

            # 2. Prepare History for B (Sanitized from A's reference pose)
            prompt_master = PromptLoader.load_formatted(
                "cinematographer_master.txt",
                setting_desc=plan.setting_desc,
                character_leader_desc=plan.character_leader_desc,
                character_follower_desc=plan.character_follower_desc,
                action=plan.scenes[0].start_pose_description
            )
            
            # Initialize history with the prompt that generated A (but without image attachment if any)
            # and A's response image.
            history = [
                types.Content(role="user", parts=[types.Part(text=prompt_master)]),
                types.Content(role="model", parts=response_a.parts)
            ]

            # 3. Keyframes B, C, D
            # We iterate through the remaining scenes.
            # Scene indices: 1 (B), 2 (C), 3 (D)
            # Map indices to Keyframe names
            keyframe_map = {1: 'B', 2: 'C', 3: 'D'}
            
            # Use len(plan.scenes) to be safer, assuming plan.scenes is ordered and corresponds to B, C, D...
            for i in range(1, len(plan.scenes)):
                if i not in keyframe_map:
                    continue # Or handle extra scenes if needed, but for now strict to logic

                key_name = keyframe_map[i]
                prompt_edit = PromptLoader.load_formatted(
                    "cinematographer_edit.txt",
                    pose_description=plan.scenes[i].start_pose_description,
                    variety_instruction=variety_instruction
                )

                response = self._generate_subsequent_keyframe(history, prompt_edit, f"Keyframe {key_name}")

                part = [p for p in response.parts if p.inline_data][0]
                assets[key_name] = self._save_image(part, f"keyframe_{key_name}.png")

                save_state(f"cinematographer_keyframe_{key_name.lower()}_complete", {
                    "path": assets[key_name],
                    "status": "success"
                }, logger)

                # Append response to history for next iteration
                history.append(types.Content(role="model", parts=response.parts))

            logger.info(f"Cinematographer: All keyframes generated successfully: {list(assets.keys())}")
            
            save_state("cinematographer_complete", {
                "assets": assets,
                "status": "success"
            }, logger)

            return assets
            
        except Exception as e:
            logger.error(f"Error generating assets: {e}", exc_info=True)
            save_state("cinematographer_error", {
                "error_type": type(e).__name__,
                "error_message": str(e)
            }, logger)
            raise
        finally:
            self.output_dir = original_output_dir
