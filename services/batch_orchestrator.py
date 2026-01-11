"""Batch processing orchestrator service.

This service handles the orchestration of batch video generation from CSV files,
following the Single Responsibility Principle by separating batch logic from main.
"""

import os
from typing import Optional, List
from dance_loop_gen.config import Config
from dance_loop_gen.core.models import CSVRow
from dance_loop_gen.services.director import DirectorService
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.services.veo import VeoService
from dance_loop_gen.services.seo_specialist import SEOSpecialistService
from dance_loop_gen.utils.csv_handler import CSVHandler
from dance_loop_gen.utils.request_builder import build_request_from_csv
from dance_loop_gen.utils.logger import setup_logger, console
from rich.rule import Rule
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

logger = setup_logger()


class BatchOrchestrator:
    """Orchestrates batch video generation from CSV files."""
    
    def __init__(
        self,
        director: DirectorService,
        cinematographer: CinematographerService,
        veo: VeoService,
        seo_specialist: SEOSpecialistService
    ):
        """Initialize the batch orchestrator.
        
        Args:
            director: Director service instance
            cinematographer: Cinematographer service instance
            veo: Veo service instance
            seo_specialist: SEO Specialist service instance
        """
        self.director = director
        self.cinematographer = cinematographer
        self.veo = veo
        self.seo_specialist = seo_specialist
    
    def resolve_csv_path(self, csv_path: str) -> Optional[str]:
        """Resolve CSV path to absolute path.
        
        Args:
            csv_path: Relative or absolute path to CSV file
            
        Returns:
            Absolute path if file exists, None otherwise
        """
        if not csv_path:
            return None
        
        # If already absolute and exists
        if os.path.isabs(csv_path) and os.path.exists(csv_path):
            return csv_path
        
        # Try resolving from current directory
        abs_path = os.path.abspath(csv_path)
        if os.path.exists(abs_path):
            return abs_path
        
        # Try resolving from project root (where main.py is)
        project_root = os.path.dirname(os.path.dirname(__file__))
        from_root = os.path.join(project_root, csv_path.lstrip('./'))
        if os.path.exists(from_root):
            return from_root
        
        return None
    
    def should_use_batch_mode(self) -> bool:
        """Determine if batch mode should be used.
        
        Returns:
            True if CSV path is configured and file exists
        """
        csv_path = self.resolve_csv_path(Config.CSV_INPUT_PATH)
        return csv_path is not None
    
    def get_pending_rows(self, csv_path: str) -> List[CSVRow]:
        """Get rows from CSV that need processing.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of pending CSV rows
            
        Raises:
            Exception if CSV cannot be read
        """
        return CSVHandler.get_pending_rows(csv_path)
    
    def create_backup(self, csv_path: str) -> Optional[str]:
        """Create backup of CSV file if configured.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            Path to backup file, or None if backup disabled
        """
        if Config.CSV_CREATE_BACKUP:
            backup_path = CSVHandler.create_backup(csv_path)
            logger.info(f"Created CSV backup: {backup_path}")
            return backup_path
        return None
    
    def process_batch(
        self,
        csv_path: str,
        base_user_request: str,
        video_processor
    ) -> None:
        """Process all pending rows from CSV file.
        
        Args:
            csv_path: Absolute path to CSV file
            base_user_request: Base template for user requests
            video_processor: Callable that processes a single video
        """
        logger.info("=" * 60)
        logger.info("BATCH PROCESSING MODE ENABLED")
        logger.info(f"CSV File: {csv_path}")
        logger.info("=" * 60)
        
        # Create backup if configured
        backup_path = self.create_backup(csv_path)
        if backup_path:
            print(f"💾 Created backup: {os.path.basename(backup_path)}")
        
        # Get pending rows
        try:
            pending_rows = self.get_pending_rows(csv_path)
            logger.info(f"Found {len(pending_rows)} pending rows to process")
            
            if len(pending_rows) == 0:
                console.print("[bold green]✔[/bold green] All rows already processed!")
                logger.info("No pending rows to process")
                return
            
            console.print(f"\n[bold blue]📋 Found {len(pending_rows)} pending videos to generate[/bold blue]\n")
            
        except Exception as e:
            logger.error(f"Failed to read CSV file: {e}", exc_info=True)
            console.print(f"[bold red]❌ Error reading CSV file:[/bold red] {e}")
            raise
        
        # Process each row with a progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            batch_task = progress.add_task("[cyan]Batch Progress", total=len(pending_rows))
            
            for idx, csv_row in enumerate(pending_rows, start=1):
                progress.update(batch_task, description=f"[cyan]Processing {idx}/{len(pending_rows)}: [italic]{csv_row.style}[/italic]")
                
                self._process_single_row(
                    csv_row,
                    idx,
                    len(pending_rows),
                    base_user_request,
                    csv_path,
                    video_processor
                )
                progress.advance(batch_task)
        
        console.print(Rule(style="bold green"))
        console.print(f"[bold green]🎉 Batch processing complete![/bold green]")
        console.print(f"Processed [bold]{len(pending_rows)}[/bold] videos")
        console.print(Rule(style="bold green"))
    
    def _process_single_row(
        self,
        csv_row: CSVRow,
        idx: int,
        total: int,
        base_user_request: str,
        csv_path: str,
        video_processor
    ) -> None:
        """Process a single CSV row.
        
        Args:
            csv_row: The CSV row to process
            idx: Current index (1-based)
            total: Total number of rows
            base_user_request: Base template for user requests
            csv_path: Path to CSV file
            video_processor: Callable that processes a single video
        """
        logger.info("=" * 60)
        logger.info(f"PROCESSING VIDEO {idx}/{total}")
        logger.info(f"Style: {csv_row.style}")
        logger.info("=" * 60)
        
        console.print(Rule(f"[bold cyan]🎬 Video {idx}/{total} [/bold cyan]", style="cyan"))
        console.print(f"[bold]Style:[/bold] {csv_row.style}")
        console.print(f"[bold]Music:[/bold] {csv_row.music}")
        
        # Build enriched request from CSV
        enriched_request = build_request_from_csv(csv_row, base_user_request)
        
        # Process the video
        try:
            output_dir = video_processor(
                enriched_request,
                self.director,
                self.cinematographer,
                self.veo,
                self.seo_specialist,
                csv_row,
                reference_pose_index=idx - 1  # Convert to 0-based index for cycling
            )
            
            logger.info(f"✅ Video {idx}/{total} completed: {output_dir}")
            console.print(f"[bold green]✅ Video {idx}/{total} completed![/bold green]")
            
            # Mark as completed in CSV
            if Config.CSV_AUTO_UPDATE:
                CSVHandler.mark_row_completed(csv_path, csv_row.row_index)
                logger.info(f"Updated CSV row {csv_row.row_index} to Created=TRUE")
                console.print(f"[italic gray]📝 Updated CSV: Row {csv_row.row_index} marked as complete[/italic gray]")
            
        except Exception as e:
            logger.error(f"❌ Failed to process video {idx}/{total}: {e}", exc_info=True)
            console.print(f"[bold red]❌ Failed to process video {idx}/{total}:[/bold red] {e}")
            console.print("[yellow]Continuing with next video...[/yellow]\n")
