import logging
import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from rich.console import Console

# Module-level state for run directory
_current_run_dir: Optional[str] = None
_run_id: Optional[str] = None

# Global Rich console instance
console = Console()

def get_run_id() -> str:
    """Get or create a run ID for this execution."""
    global _run_id
    if _run_id is None:
        _run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _run_id

def get_log_dir() -> str:
    """Get the log directory path (inside dance_loop_gen folder)."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

def get_run_dir() -> str:
    """Get the run-specific directory for logs and state files."""
    global _current_run_dir
    if _current_run_dir is None:
        run_id = get_run_id()
        _current_run_dir = os.path.join(get_log_dir(), f"run_{run_id}")
        os.makedirs(_current_run_dir, exist_ok=True)
    return _current_run_dir

def save_state(step_name: str, state: Dict[str, Any], logger: Optional[logging.Logger] = None) -> str:
    """
    Save application state to a JSON file.
    
    Args:
        step_name: Name of the current step (e.g., 'plan_generated', 'keyframe_a')
        state: Dictionary containing state data to serialize
        logger: Optional logger for logging the save operation
    
    Returns:
        Path to the saved state file
    """
    run_dir = get_run_dir()
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"state_{timestamp}_{step_name}.json"
    filepath = os.path.join(run_dir, filename)
    
    # Convert non-serializable objects to strings
    def serialize(obj: Any) -> Any:
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, '__dict__'):
            return {k: serialize(v) for k, v in obj.__dict__.items() if not k.startswith('_')}
        elif isinstance(obj, dict):
            return {k: serialize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [serialize(item) for item in obj]
        elif isinstance(obj, bytes):
            return f"<bytes: {len(obj)} bytes>"
        else:
            try:
                json.dumps(obj)
                return obj
            except (TypeError, ValueError):
                return str(obj)
    
    serialized_state = serialize(state)
    
    with open(filepath, 'w') as f:
        json.dump(serialized_state, f, indent=2, default=str)
    
    if logger:
        logger.info(f"State saved: {filepath}")
    
    return filepath

def setup_logger(name: str = "dance_loop_gen", log_dir: str = None):
    """
    Set up the application logger with file and console handlers.
    
    Args:
        name: Logger name
        log_dir: Override log directory (uses run-specific dir by default)
    
    Returns:
        Configured logger instance
    """
    run_dir = get_run_dir()
    log_file = os.path.join(run_dir, "app.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Only add handlers if not already added
    if not logger.handlers:
        # File Handler - DEBUG level (everything)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)

        # Console Handler - INFO level 
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
