"""Video processor service for single video generation.

Handles the complete workflow for generating a single dance video,
following SOLID principles by separating processing logic from orchestration.
"""

import os
import re
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel
from dance_loop_gen.config import Config
from dance_loop_gen.core.models import CSVRow
from dance_loop_gen.services.director import DirectorService
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.services.veo import VeoService
from dance_loop_gen.services.seo_specialist import SEOSpecialistService
from dance_loop_gen.utils.logger import setup_logger, save_state

logger = setup_logger()

class VideoProcessingResult(BaseModel):
    """Encapsulates the result of a video processing run."""
    output_dir: str
    plan_title: str
    plan_description: str
    scene_count: int
    tags: List[str]
    assets: Dict[str, str]
    recommended_metadata_option: Optional[int] = None


class VideoProcessor:
    """Processes a single video generation from start to finish."""
    
    @staticmethod
    def process(
        user_request: str,
        director: DirectorService,
        cinematographer: CinematographerService,
        veo: VeoService,
        seo_specialist: SEOSpecialistService,
        csv_row: Optional[CSVRow] = None,
        reference_pose_index: int = 0
    ) -> VideoProcessingResult:
        """Process a single video generation from start to finish.
        
        Args:
            user_request: The enriched user request
            director: Director service instance
            cinematographer: Cinematographer service instance
            veo: Veo service instance
            seo_specialist: SEO Specialist service instance
            csv_row: Optional CSV row data (for batch processing)
            reference_pose_index: Index for selecting reference pose (for batch iteration)
            
        Returns:
            VideoProcessingResult object containing generation details.
            
        Raises:
            Exception if video generation fails
        """
        # 1. Generate Plan
        logger.info("Generating video plan via Director...")
        project_plan = director.generate_plan(user_request)
        logger.info(f"Plan generated successfully: {project_plan.title}")
        logger.debug(f"Plan scenes: {len(project_plan.scenes)}")
        
        save_state("03_plan_generated", {
            "plan": project_plan,
            "title": project_plan.title,
            "scenes_count": len(project_plan.scenes)
        }, logger)
        
        # 2. Create Output Directory
        run_output_dir = VideoProcessor._create_output_directory(project_plan.title)
        logger.info(f"Creating output directory: {run_output_dir}")
        print(f"📂 Output directory: {run_output_dir}")
        
        save_state("04_output_dir", {
            "output_dir": run_output_dir,
            "safe_title": os.path.basename(run_output_dir)
        }, logger)
        
        # 3. Generate Assets
        logger.info("Generating keyframe assets via Cinematographer...")
        
        # Extract scene variety from CSV row if available
        scene_variety = csv_row.scene_variety if csv_row and csv_row.scene_variety is not None else None
        
        keyframe_assets = cinematographer.generate_assets(
            project_plan,
            output_dir=run_output_dir,
            scene_variety=scene_variety,
            reference_pose_index=reference_pose_index
        )
        logger.info(f"Assets generated: {list(keyframe_assets.keys())}")
        
        save_state("05_assets_generated", {
            "assets": keyframe_assets,
            "assets_count": len(keyframe_assets)
        }, logger)
        
        # 4. Generate Veo Instructions
        logger.info("Generating Veo instructions...")
        veo.generate_instructions(project_plan, keyframe_assets, output_dir=run_output_dir)
        
        # 5. Generate SEO Metadata
        recommended_metadata_option = VideoProcessor._generate_metadata(
            project_plan,
            seo_specialist,
            run_output_dir
        )
        
        # 6. Save Completion State
        save_state("08_complete", {
            "status": "complete",
            "output_dir": run_output_dir,
            "assets": keyframe_assets,
            "plan_title": project_plan.title
        }, logger)
        
        return VideoProcessingResult(
            output_dir=run_output_dir,
            plan_title=project_plan.title,
            plan_description=project_plan.description,
            scene_count=len(project_plan.scenes),
            tags=project_plan.backend_tags,
            assets=keyframe_assets,
            recommended_metadata_option=recommended_metadata_option
        )
    
    @staticmethod
    def _create_output_directory(title: str) -> str:
        """Create a run-specific output directory.
        
        Args:
            title: The video plan title
            
        Returns:
            Absolute path to the output directory
        """
        # Sanitize title for filesystem
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().lower()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return os.path.join(Config.OUTPUT_DIR, f"{safe_title}_{timestamp}")
    
    @staticmethod
    def _generate_metadata(
        project_plan,
        seo_specialist: SEOSpecialistService,
        output_dir: str
    ) -> Optional[int]:
        """Generate SEO metadata for the video.
        
        Args:
            project_plan: The video plan
            seo_specialist: SEO Specialist service instance
            output_dir: Output directory for metadata files

        Returns:
            The recommended option number if successful, None otherwise.
        """
        logger.info("Generating metadata alternatives via SEO Specialist...")
        try:
            metadata_config = seo_specialist.load_config()
            metadata_alternatives = seo_specialist.generate_alternatives(
                project_plan,
                metadata_config
            )
            json_path, csv_path = seo_specialist.save_metadata(
                metadata_alternatives,
                output_dir
            )
            
            save_state("07_metadata_generated", {
                "json_path": json_path,
                "csv_path": csv_path,
                "recommended": metadata_alternatives.recommended,
                "reasoning": metadata_alternatives.reasoning
            }, logger)
            
            return metadata_alternatives.recommended

        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}", exc_info=True)
            print(f"⚠️ Warning: Failed to generate metadata alternatives: {e}")
            return None
