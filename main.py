"""Main entry point for Dance Loop Gen.

This module provides a clean entry point following SOLID principles.
Services are responsible for their own logic, and main.py only coordinates.
"""

import sys
from google import genai
from dance_loop_gen.config import Config
from dance_loop_gen.services.director import DirectorService
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.services.veo import VeoService
from dance_loop_gen.services.seo_specialist import SEOSpecialistService
from dance_loop_gen.services.batch_orchestrator import BatchOrchestrator
from dance_loop_gen.services.video_processor import VideoProcessor
from dance_loop_gen.services.report_service import ReportService
from dance_loop_gen.utils.prompt_loader import PromptLoader
from dance_loop_gen.utils.logger import setup_logger, save_state, get_run_dir, console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

# Initialize logger
logger = setup_logger()


def initialize_services(client: genai.Client) -> tuple:
    """Initialize all required services.
    
    Args:
        client: Initialized Gemini client
        
    Returns:
        Tuple of (director, cinematographer, veo, seo_specialist, batch_orchestrator)
    """
    with console.status("[bold blue]Initializing services...", spinner="dots"):
        director = DirectorService(client)
        cinematographer = CinematographerService(client)
        veo = VeoService()
        seo_specialist = SEOSpecialistService(client)
        report_service = ReportService()
        batch_orchestrator = BatchOrchestrator(
            director,
            cinematographer,
            veo,
            seo_specialist,
            report_service
        )
        logger.info("All services initialized")
    
    console.print("[green]✔[/green] Services initialized successfully")
    
    # Mode Announcement
    if batch_orchestrator.should_use_batch_mode():
        console.print(Panel("[bold cyan]🔄 BATCH PROCESSING MODE DETECTED[/bold cyan]", border_style="cyan"))
        logger.info("Application detected Batch Mode via CSV_INPUT_PATH")
    else:
        # Check if CSV path was actually set but missing
        if Config.CSV_INPUT_PATH:
            console.print(Panel(f"[bold yellow]⚠ BATCH MODE ATTEMPTED BUT FAILED[/bold yellow]\nCSV file not found: [italic]{Config.CSV_INPUT_PATH}[/italic]\n\n[bold white]Falling back to SINGLE mode...[/bold white]", title="Warning", border_style="yellow"))
            logger.warning(f"Batch mode was configured but CSV file was missing: {Config.CSV_INPUT_PATH}")
        else:
            console.print(Panel("[bold magenta]🎯 SINGLE VIDEO MODE[/bold magenta]", border_style="magenta"))
            logger.info("Application starting in Single Mode")
            
    return director, cinematographer, veo, seo_specialist, batch_orchestrator, report_service


def validate_and_log_config():
    """Validate configuration and log settings."""
    logger.info("Validating configuration...")
    Config.validate()
    
    logger.info("Configuration validated successfully")
    logger.debug(f"GEMINI_VERSION: {Config.GEMINI_VERSION}")
    logger.debug(f"MODEL_NAME_TEXT: {Config.MODEL_NAME_TEXT}")
    logger.debug(f"MODEL_NAME_IMAGE: {Config.MODEL_NAME_IMAGE}")
    logger.debug(f"OUTPUT_DIR: {Config.OUTPUT_DIR}")
    logger.debug(f"PROMPTS_DIR: {Config.PROMPTS_DIR}")
    logger.debug(f"CSV_INPUT_PATH: {Config.CSV_INPUT_PATH}")
    
    save_state("01_config", {
        "gemini_version": Config.GEMINI_VERSION,
        "model_name_text": Config.MODEL_NAME_TEXT,
        "model_name_image": Config.MODEL_NAME_IMAGE,
        "output_dir": Config.OUTPUT_DIR,
        "prompts_dir": Config.PROMPTS_DIR,
        "csv_input_path": Config.CSV_INPUT_PATH,
    }, logger)


def load_base_user_request() -> str:
    """Load the base user request template.
    
    Returns:
        Base user request string
    """
    logger.info("Loading user request template...")
    try:
        user_request = PromptLoader.load("default_user_request.txt")
        logger.info(f"Loaded user request template ({len(user_request)} characters)")
        logger.debug(f"User request preview: {user_request[:200]}...")
        return user_request
    except FileNotFoundError:
        logger.warning("default_user_request.txt not found. Using empty request.")
        console.print("[yellow]⚠[/yellow] Warning: [italic]default_user_request.txt[/italic] not found. Using empty request.")
        return ""


def run_single_mode(
    base_user_request: str,
    director: DirectorService,
    cinematographer: CinematographerService,
    veo: VeoService,
    seo_specialist: SEOSpecialistService,
    report_service: ReportService
):
    """Run application in single video generation mode.
    
    Args:
        base_user_request: Base user request template
        director: Director service instance
        cinematographer: Cinematographer service instance
        veo: Veo service instance
        seo_specialist: SEO Specialist service instance
        report_service: Report service instance
    """
    logger.info("=" * 60)
    logger.info("SINGLE PROCESSING MODE")
    logger.info("=" * 60)
    
    console.print(Rule("[bold magenta]Single Processing Mode[/bold magenta]", style="magenta"))
    
    save_state("02_user_request", {
        "user_request": base_user_request,
        "request_length": len(base_user_request)
    }, logger)
    
    try:
        output_dir = VideoProcessor.process(
            base_user_request,
            director,
            cinematographer,
            veo,
            seo_specialist,
            None,
            reference_pose_index=0,
            report_service=report_service
        )
        
        console.print(Panel(
            f"[bold green]Generation complete![/bold green]\n\n[bold]Output:[/bold] [cyan]{output_dir}[/cyan]",
            title="Success",
            expand=False
        ))
        
    except Exception as e:
        logger.error(f"Failed to process video: {e}", exc_info=True)
        console.print(f"[bold red]❌ Failed to generate video:[/bold red] {e}")
        sys.exit(1)


def run_batch_mode(
    base_user_request: str,
    batch_orchestrator: BatchOrchestrator
):
    """Run application in batch processing mode.
    
    Args:
        base_user_request: Base user request template
        batch_orchestrator: Batch orchestrator service instance
    """
    csv_path = batch_orchestrator.resolve_csv_path(Config.CSV_INPUT_PATH)
    
    if not csv_path:
        logger.error(f"CSV file not found: {Config.CSV_INPUT_PATH}")
        console.print(f"[bold red]❌ CSV file not found:[/bold red] {Config.CSV_INPUT_PATH}")
        sys.exit(1)
    
    try:
        batch_orchestrator.process_batch(
            csv_path,
            base_user_request,
            VideoProcessor.process
        )
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        console.print(f"[bold red]❌ Batch processing failed:[/bold red] {e}")
        sys.exit(1)


def main():
    """Main application entry point."""
    logger.info("=" * 60)
    logger.info("DANCE LOOP GEN - Starting Application")
    logger.info("=" * 60)
    
    run_dir = get_run_dir()
    logger.info(f"Run directory: {run_dir}")
    
    # Step 1: Validate Configuration
    try:
        validate_and_log_config()
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        sys.exit(1)
    
    # Step 2: Initialize Gemini Client
    logger.info("Initializing Gemini client...")
    logger.debug(f"API version: {Config.GEMINI_VERSION}")
    client = genai.Client(http_options={'api_version': Config.GEMINI_VERSION})
    logger.info("Gemini client initialized successfully")
    
    # Step 3: Initialize Services
    director, cinematographer, veo, seo_specialist, batch_orchestrator, report_service = \
        initialize_services(client)
    
    # Step 4: Load Base User Request
    base_user_request = load_base_user_request()
    
    # Step 5: Determine Mode and Execute
    if batch_orchestrator.should_use_batch_mode():
        run_batch_mode(base_user_request, batch_orchestrator)
    else:
        run_single_mode(
            base_user_request,
            director,
            cinematographer,
            veo,
            seo_specialist,
            report_service
        )


if __name__ == "__main__":
    main()
