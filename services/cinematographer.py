import os
import base64
from typing import Dict, List, Any
from google import genai
from google.genai import types
from core.interfaces import ICinematographer
from core.models import VideoPlan
from config import Config
from utils.prompt_loader import PromptLoader
from utils.logger import setup_logger, save_state

logger = setup_logger()

class CinematographerService(ICinematographer):
    def __init__(self, client: genai.Client):
        self.client = client
        self.output_dir = Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load reference pose images
        self.reference_poses = self._load_reference_poses()

        logger.debug(f"CinematographerService initialized with output_dir: {self.output_dir}")
        logger.info(f"Loaded {len(self.reference_poses)} reference pose(s)")

    def _load_reference_poses(self) -> List[Any]:
        """Loads reference poses with fallback logic."""
        # 1. Try loading all images from the reference_images folder first
        poses = PromptLoader.load_images_from_directory(Config.REFERENCE_IMAGES_DIR)
        
        # 2. If folder is empty/missing, fall back to "reference_pose" pattern in prompts dir
        if not poses:
            poses = PromptLoader.load_multiple_images("reference_pose")
        
        # 3. Last resort: fall back to single "reference_pose.png/jpg"
        if not poses:
            for ext in [".png", ".jpg", ".jpeg"]:
                single_pose = PromptLoader.load_optional_image(f"reference_pose{ext}")
                if single_pose:
                    poses = [single_pose]
                    break
        return poses
    
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
        logger.info(f"Attempting to save {filename}...")
        
        # Log available attributes on the part
        logger.debug(f"Part attributes: {dir(part)}")
        
        if part.inline_data:
            logger.debug(f"Found inline_data. MimeType: {part.inline_data.mime_type}")
            try:
                data = part.inline_data.data
                logger.debug(f"Data type: {type(data)}")
                
                if isinstance(data, bytes):
                    image_data = data
                    logger.debug("Data is bytes, using directly.")
                else:
                    # Assume string -> base64
                    image_data = base64.b64decode(data)
                    logger.debug("Data is string, decoded base64.")

                logger.debug(f"Final data size: {len(image_data)} bytes.")
                if len(image_data) < 1000:
                    logger.warning("Warning: Saved image is unusually small (<1KB).")
                
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(image_data)
                
                logger.info(f"Saved: {filepath}")
                return filepath
            except Exception as e:
                logger.error(f"Error saving {filename}: {e}", exc_info=True)
                raise
        else:
            logger.warning(f"No inline_data found for {filename}. Inspecting full part...")
            logger.debug(f"Part content: {part}")
            
        return None

    def _generate_keyframe_a(self, plan: VideoPlan, reference_pose_index: int) -> tuple[str, Any]:
        """Generates Keyframe A (Master) using optional reference pose."""
        logger.info("--- Generating Keyframe A (Master) ---")
        prompt_a = PromptLoader.load_formatted(
            "cinematographer_master.txt",
            setting_desc=plan.setting_desc,
            character_leader_desc=plan.character_leader_desc,
            character_follower_desc=plan.character_follower_desc,
            action=plan.scenes[0].start_pose_description
        )

        # Build contents for API call with selected reference pose
        contents_a = prompt_a
        if self.reference_poses:
            # Select reference pose based on index (cycle if needed)
            pose_idx = reference_pose_index % len(self.reference_poses)
            image_bytes, mime_type = self.reference_poses[pose_idx]

            logger.info(f"Using reference pose {pose_idx + 1}/{len(self.reference_poses)}")
            print(f"   📷 Using reference pose {pose_idx + 1}/{len(self.reference_poses)}")

            # Add instruction to use the reference pose
            reference_instruction = (
                "\n\nIMPORTANT: Use the attached reference image as a guide for:\n"
                "- The FRAMING and COMPOSITION (shot type, camera angle, how much of the frame the dancers occupy)\n"
                "- The position and pose of the dancers\n"
                "- The body positions and spatial arrangement\n"
                "Apply the character descriptions and setting from above while maintaining the reference image's framing and pose structure."
            )
            prompt_a_with_ref = prompt_a + reference_instruction

            contents_a = [
                prompt_a_with_ref,
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            ]

        print("   Generating Keyframe A (Master)...")
        logger.info(f"Calling Gemini API for Keyframe A (model: {Config.MODEL_NAME_IMAGE})")

        response_a = self.client.models.generate_content(
            model=Config.MODEL_NAME_IMAGE,
            contents=contents_a,
            config=types.GenerateContentConfig(
                image_config=types.ImageConfig(aspect_ratio="9:16")
            )
        )

        logger.info("Keyframe A API response received")
        part_a = [p for p in response_a.parts if p.inline_data][0]
        path_a = self._save_image(part_a, "keyframe_A.png")

        save_state("cinematographer_keyframe_a_complete", {
            "path": path_a,
            "status": "success"
        }, logger)

        return path_a, response_a.parts

    def _generate_sequential_keyframes(self, plan: VideoPlan, variety_instruction: str, previous_response_parts: Any) -> Dict[str, str]:
        """Generates subsequent keyframes (B-H) using conversational editing."""
        assets = {}
        current_history = None

        # Map indices to Keyframe letters
        keyframe_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

        # Process remaining scenes (B, C, D...)
        for i, scene in enumerate(plan.scenes[1:], start=1):
            if i >= len(keyframe_letters):
                logger.warning(f"Scene index {i} exceeds supported keyframe letters. Skipping.")
                break

            keyframe_letter = keyframe_letters[i]
            logger.info(f"--- Generating Keyframe {keyframe_letter} (via Editing) ---")

            # Load edit prompt
            prompt_edit = PromptLoader.load_formatted(
                "cinematographer_edit.txt",
                pose_description=scene.start_pose_description,
                variety_instruction=variety_instruction
            )

            print(f"   Generating Keyframe {keyframe_letter} (via Editing)...")

            # Special handling for Keyframe B: Reset history to exclude reference pose
            if keyframe_letter == 'B':
                # Create a new prompt that describes the previous scene (A) without reference pose
                prompt_base = PromptLoader.load_formatted(
                    "cinematographer_master.txt",
                    setting_desc=plan.setting_desc,
                    character_leader_desc=plan.character_leader_desc,
                    character_follower_desc=plan.character_follower_desc,
                    action=plan.scenes[0].start_pose_description
                )

                # Build NEW conversation history
                current_history = [
                    types.Content(role="user", parts=[types.Part(text=prompt_base)]),
                    types.Content(role="model", parts=previous_response_parts),
                    types.Content(role="user", parts=[types.Part(text=prompt_edit)])
                ]
                logger.debug("History reset for Keyframe B (without reference pose)")

            else:
                # Append to existing history
                current_history.extend([
                    types.Content(role="model", parts=previous_response_parts),
                    types.Content(role="user", parts=[types.Part(text=prompt_edit)])
                ])

            # Generate content
            response = self.client.models.generate_content(
                model=Config.MODEL_NAME_IMAGE,
                contents=list(current_history)
            )

            logger.info(f"Keyframe {keyframe_letter} API response received")

            # Save asset
            part = [p for p in response.parts if p.inline_data][0]
            path = self._save_image(part, f"keyframe_{keyframe_letter}.png")
            assets[keyframe_letter] = path

            save_state(f"cinematographer_keyframe_{keyframe_letter.lower()}_complete", {
                "path": path,
                "status": "success"
            }, logger)

            # Update for next iteration
            previous_response_parts = response.parts

        return assets

    def generate_assets(self, plan: VideoPlan, output_dir: str = None, scene_variety: int = None, reference_pose_index: int = 0) -> Dict[str, str]:
        logger.info("=" * 40)
        logger.info("Cinematographer: Starting asset generation")
        logger.info("=" * 40)
        
        # Setup output directory
        target_dir = output_dir if output_dir else self.output_dir
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Target output directory: {target_dir}")
        
        original_output_dir = self.output_dir
        self.output_dir = target_dir
        
        # Determine variety
        effective_variety = scene_variety if scene_variety is not None else Config.SCENE_VARIETY
        variety_instruction = self._build_variety_instruction(effective_variety)
        
        save_state("cinematographer_start", {
            "target_dir": target_dir,
            "plan_title": plan.title,
            "scenes_count": len(plan.scenes),
            "scene_variety": effective_variety
        }, logger)
        
        try:
            assets = {}
            
            # 1. GENERATE KEYFRAME A
            path_a, parts_a = self._generate_keyframe_a(plan, reference_pose_index)
            assets['A'] = path_a
            
            # 2. GENERATE SEQUENTIAL KEYFRAMES
            sequential_assets = self._generate_sequential_keyframes(plan, variety_instruction, parts_a)
            assets.update(sequential_assets)

            logger.info("=" * 40)
            logger.info("Cinematographer: All keyframes generated successfully")
            logger.info(f"Assets: {assets}")
            logger.info("=" * 40)
            
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
