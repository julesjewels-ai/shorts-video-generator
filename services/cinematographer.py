import os
import base64
from typing import Dict, List
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
        """Build scene variation instructions based on variety level (0-10).
        
        Args:
            variety: Scene variety level (0=minimal, 10=dramatic)
            
        Returns:
            Instruction string for AI to control background variation
        """
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

    def generate_assets(self, plan: VideoPlan, output_dir: str = None, scene_variety: int = None, reference_pose_index: int = 0) -> Dict[str, str]:
        logger.info("=" * 40)
        logger.info("Cinematographer: Starting asset generation")
        logger.info("=" * 40)
        
        # Use provided output_dir or fallback to default
        target_dir = output_dir if output_dir else self.output_dir
        os.makedirs(target_dir, exist_ok=True)
        logger.info(f"Target output directory: {target_dir}")
        
        # Update self.output_dir for this run so _save_image uses it
        original_output_dir = self.output_dir
        self.output_dir = target_dir
        
        logger.debug(f"Plan title: {plan.title}")
        logger.debug(f"Setting: {plan.setting_desc[:100]}...")
        logger.debug(f"Scenes count: {len(plan.scenes)}")
        
        # Determine effective scene variety level
        effective_variety = scene_variety if scene_variety is not None else Config.SCENE_VARIETY
        variety_instruction = self._build_variety_instruction(effective_variety)
        
        logger.info(f"Scene variety level: {effective_variety}/10")
        logger.debug(f"Variety instruction: {variety_instruction[:100]}...")
        
        save_state("cinematographer_start", {
            "target_dir": target_dir,
            "plan_title": plan.title,
            "scenes_count": len(plan.scenes),
            "scene_variety": effective_variety
        }, logger)
        
        try:
            assets = {}
            
            # 1. GENERATE KEYFRAME A (The Anchor)
            logger.info("--- Generating Keyframe A (Master) ---")
            prompt_a = PromptLoader.load_formatted(
                "cinematographer_master.txt",
                setting_desc=plan.setting_desc,
                character_leader_desc=plan.character_leader_desc,
                character_follower_desc=plan.character_follower_desc,
                action=plan.scenes[0].start_pose_description
            )
            
            # Build contents for API call with selected reference pose
            if self.reference_poses:
                # Select reference pose based on index (cycle if needed)
                pose_idx = reference_pose_index % len(self.reference_poses)
                image_bytes, mime_type = self.reference_poses[pose_idx]
                
                logger.info(f"Using reference pose {pose_idx + 1}/{len(self.reference_poses)}")
                
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
                logger.debug(f"Prompt A (with reference) length: {len(prompt_a_with_ref)} chars")
            else:
                contents_a = prompt_a
                logger.debug(f"Prompt A length: {len(prompt_a)} chars")
            
            logger.debug(f"Prompt A preview: {prompt_a[:200]}...")
            
            save_state("cinematographer_keyframe_a_prompt", {
                "prompt": prompt_a,
                "prompt_length": len(prompt_a),
                "has_reference_pose": len(self.reference_poses) > 0,
                "reference_pose_index": reference_pose_index if self.reference_poses else None
            }, logger)
            
            print("   Generating Keyframe A (Master)...")
            if self.reference_poses:
                pose_idx = reference_pose_index % len(self.reference_poses)
                print(f"   📷 Using reference pose {pose_idx + 1}/{len(self.reference_poses)}")
            logger.info(f"Calling Gemini API for Keyframe A (model: {Config.MODEL_NAME_IMAGE})")
            
            response_a = self.client.models.generate_content(
                model=Config.MODEL_NAME_IMAGE,
                contents=contents_a,
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(aspect_ratio="9:16")
                )
            )
            
            logger.info("Keyframe A API response received")
            logger.debug(f"Response parts count: {len(response_a.parts)}")
            
            part_a = [p for p in response_a.parts if p.inline_data][0]
            path_a = self._save_image(part_a, "keyframe_A.png")
            assets['A'] = path_a
            
            save_state("cinematographer_keyframe_a_complete", {
                "path": path_a,
                "status": "success"
            }, logger)
            
            # 2. GENERATE KEYFRAME B (Editing Keyframe A)
            logger.info("--- Generating Keyframe B (via Editing) ---")
            
            # Create a new prompt that describes the previous scene without reference pose
            prompt_b_base = PromptLoader.load_formatted(
                "cinematographer_master.txt",
                setting_desc=plan.setting_desc,
                character_leader_desc=plan.character_leader_desc,
                character_follower_desc=plan.character_follower_desc,
                action=plan.scenes[0].start_pose_description
            )
            
            # Add the editing instruction for the new pose
            prompt_b_edit = PromptLoader.load_formatted(
                "cinematographer_edit.txt",
                pose_description=plan.scenes[1].start_pose_description,
                variety_instruction=variety_instruction
            )
            
            logger.debug(f"Prompt B base length: {len(prompt_b_base)} chars")
            logger.debug(f"Prompt B edit length: {len(prompt_b_edit)} chars")
            
            save_state("cinematographer_keyframe_b_prompt", {
                "prompt_base": prompt_b_base,
                "prompt_edit": prompt_b_edit,
                "prompt_length": len(prompt_b_base) + len(prompt_b_edit)
            }, logger)
            
            print("   Generating Keyframe B (New Scene)...")
            logger.info(f"Calling Gemini API for Keyframe B - new conversation without reference pose")
            
            # Build a NEW conversation history that excludes the reference pose image
            # This ensures Keyframe B is not influenced by the reference pose
            history_b = [
                types.Content(role="user", parts=[types.Part(text=prompt_b_base)]),
                types.Content(role="model", parts=response_a.parts),  # Contains Keyframe A image
                types.Content(role="user", parts=[types.Part(text=prompt_b_edit)])
            ]
            logger.debug(f"History B length: {len(history_b)} messages (without reference pose)")
            
            response_b = self.client.models.generate_content(
                model=Config.MODEL_NAME_IMAGE,
                contents=history_b
            )
            
            logger.info("Keyframe B API response received")
            logger.debug(f"Response parts count: {len(response_b.parts)}")
            
            part_b = [p for p in response_b.parts if p.inline_data][0]
            path_b = self._save_image(part_b, "keyframe_B.png")
            assets['B'] = path_b
            
            save_state("cinematographer_keyframe_b_complete", {
                "path": path_b,
                "status": "success"
            }, logger)

            # 3. GENERATE KEYFRAME C (Editing Keyframe B)
            logger.info("--- Generating Keyframe C (via Editing) ---")
            prompt_c = PromptLoader.load_formatted(
                "cinematographer_edit.txt",
                pose_description=plan.scenes[2].start_pose_description,
                variety_instruction=variety_instruction
            )
            logger.debug(f"Prompt C length: {len(prompt_c)} chars")
            
            save_state("cinematographer_keyframe_c_prompt", {
                "prompt": prompt_c,
                "prompt_length": len(prompt_c)
            }, logger)
            
            print("   Generating Keyframe C (via Editing)...")
            logger.info(f"Calling Gemini API for Keyframe C with full conversation history")
            
            history_c = history_b + [
                types.Content(role="model", parts=response_b.parts),  # Contains Sig B
                types.Content(role="user", parts=[types.Part(text=prompt_c)])
            ]
            logger.debug(f"History C length: {len(history_c)} messages")
            
            response_c = self.client.models.generate_content(
                model=Config.MODEL_NAME_IMAGE,
                contents=history_c
            )
            
            logger.info("Keyframe C API response received")
            logger.debug(f"Response parts count: {len(response_c.parts)}")
            
            part_c = [p for p in response_c.parts if p.inline_data][0]
            path_c = self._save_image(part_c, "keyframe_C.png")
            assets['C'] = path_c
            
            save_state("cinematographer_keyframe_c_complete", {
                "path": path_c,
                "status": "success"
            }, logger)

            # 4. GENERATE KEYFRAME D (Editing Keyframe C)
            logger.info("--- Generating Keyframe D (via Editing) ---")
            prompt_d = PromptLoader.load_formatted(
                "cinematographer_edit.txt",
                pose_description=plan.scenes[3].start_pose_description,
                variety_instruction=variety_instruction
            )
            logger.debug(f"Prompt D length: {len(prompt_d)} chars")
            
            save_state("cinematographer_keyframe_d_prompt", {
                "prompt": prompt_d,
                "prompt_length": len(prompt_d)
            }, logger)
            
            print("   Generating Keyframe D (via Editing)...")
            logger.info(f"Calling Gemini API for Keyframe D with full conversation history")
            
            history_d = history_c + [
                types.Content(role="model", parts=response_c.parts),  # Contains Keyframe C
                types.Content(role="user", parts=[types.Part(text=prompt_d)])
            ]
            logger.debug(f"History D length: {len(history_d)} messages")
            
            response_d = self.client.models.generate_content(
                model=Config.MODEL_NAME_IMAGE,
                contents=history_d
            )
            
            logger.info("Keyframe D API response received")
            logger.debug(f"Response parts count: {len(response_d.parts)}")
            
            part_d = [p for p in response_d.parts if p.inline_data][0]
            path_d = self._save_image(part_d, "keyframe_D.png")
            assets['D'] = path_d
            
            save_state("cinematographer_keyframe_d_complete", {
                "path": path_d,
                "status": "success"
            }, logger)

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
