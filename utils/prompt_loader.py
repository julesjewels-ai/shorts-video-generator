import os
import mimetypes
from typing import Any, Optional, Tuple
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError, validator

class PromptFile(BaseModel):
    """Validator for prompt filenames to prevent path traversal."""
    filename: str = Field(..., description="The name of the file to load")

    @validator('filename')
    def validate_filename(cls, v: str) -> str:
        # Prevent absolute paths
        if os.path.isabs(v):
            raise ValueError("Absolute paths are not allowed")

        # Prevent traversal
        if '..' in v.split(os.sep) or '..' in v.split(os.altsep or os.sep):
            raise ValueError("Path traversal is not allowed")

        return v

class PromptLoader:
    @staticmethod
    def _validate_path(filename: str) -> Path:
        """
        Validates that the filename is safe and resides within the prompts directory.
        Returns the resolved Path object.
        """
        from ..config import Config

        # Use Pydantic to validate the input structure
        try:
            model = PromptFile(filename=filename)
        except ValidationError as e:
            # Re-raise as ValueError for cleaner error handling in callers
            raise ValueError(f"Invalid filename: {e}")

        # Resolve paths
        prompts_dir = Path(Config.PROMPTS_DIR).resolve()

        # Handle cases where filename might have separators
        # We join and then resolve
        target_path = (prompts_dir / model.filename).resolve()

        # Strict check: ensure the resolved path starts with the prompts directory
        if not target_path.is_relative_to(prompts_dir):
            raise ValueError(f"Security Alert: Attempted path traversal to {target_path}")

        return target_path

    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        path = PromptLoader._validate_path(filename)
        
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
            
    @staticmethod
    def load_formatted(filename: str, **kwargs: Any) -> str:
        """Loads and formats a prompt with the given keyword arguments."""
        content = PromptLoader.load(filename)
        return content.format(**kwargs)

    @staticmethod
    def load_optional(filename: str) -> Optional[str]:
        """Loads a prompt file, returning None if missing or empty.
        
        This is useful for optional configuration files like outfit descriptions
        where the user may leave them blank to let the AI decide.
        """
        try:
            path = PromptLoader._validate_path(filename)
            if not path.exists():
                return None

            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else None
        except (ValueError, FileNotFoundError):
            # If path validation fails or file not found
            return None

    @staticmethod
    def load_optional_image(filename: str) -> Optional[Tuple[bytes, str]]:
        """Loads an optional image file from the prompts directory.
        
        This is useful for optional reference images like pose references
        where the user may leave them blank to let the AI decide.
        
        Args:
            filename: Name of the image file (e.g., 'reference_pose.png')
            
        Returns:
            Tuple of (image_bytes, mime_type) if file exists, None otherwise.
        """
        # We can't reuse _validate_path directly because this method tries extensions
        from ..config import Config  # Lazy import to avoid circular dependency
        
        # Validate base filename first
        try:
            PromptFile(filename=filename)
        except ValidationError:
            return None

        prompts_dir = Path(Config.PROMPTS_DIR).resolve()
        
        # Helper to check and read
        def try_read(p: Path) -> Optional[Tuple[bytes, str]]:
            if not p.exists():
                return None
            
            if not p.is_relative_to(prompts_dir):
                return None # Security check failed

            mime_type, _ = mimetypes.guess_type(p)
            if not mime_type or not mime_type.startswith('image/'):
                return None

            with open(p, "rb") as f:
                image_bytes = f.read()
            return (image_bytes, mime_type) if image_bytes else None

        # 1. Try exact path
        path = (prompts_dir / filename).resolve()
        result = try_read(path)
        if result:
            return result
            
        # 2. Try extensions if no extension provided
        if not path.suffix:
            for ext in [".png", ".jpg", ".jpeg"]:
                test_path = path.with_suffix(ext)
                result = try_read(test_path)
                if result:
                    return result

        return None

    @staticmethod
    def load_multiple_images(pattern: str) -> list:
        """Loads multiple image files matching a pattern from the prompts directory.
        
        This is useful for loading multiple reference poses (e.g., reference_pose_*.png)
        where the user wants to iterate through different poses for batch processing.
        
        Args:
            pattern: Pattern for the base filename (e.g., 'reference_pose')
                    Will search for files like 'reference_pose_1.png', 'reference_pose_2.png', etc.
            
        Returns:
            List of tuples of (image_bytes, mime_type), sorted by filename.
            Empty list if no matching files found.
        """
        from ..config import Config  # Lazy import to avoid circular dependency
        import glob
        
        # Validate pattern to prevent traversal in glob
        try:
            PromptFile(filename=pattern)
        except ValidationError:
            return []

        prompts_dir = Path(Config.PROMPTS_DIR).resolve()

        # Build search pattern for numbered files
        matching_files = []
        for ext in ["png", "jpg", "jpeg", "jpe"]:
            # Securely construct glob pattern
            # Note: glob.glob can be dangerous if pattern contains wildcards/traversal
            # But we validated 'pattern' above.
            # However, we must ensure the glob doesn't escape.

            search_pattern = prompts_dir / f"{pattern}_*.{ext}"
            matching_files.extend(glob.glob(str(search_pattern)))
        
        if not matching_files:
            return []
        
        # Sort to ensure consistent ordering (1, 2, 3, ...)
        matching_files.sort()
        
        images = []
        for file_path_str in matching_files:
            path = Path(file_path_str).resolve()

            # Security check for each found file
            if not path.is_relative_to(prompts_dir):
                continue

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type or not mime_type.startswith('image/'):
                continue
                
            try:
                with open(path, "rb") as f:
                    image_bytes = f.read()
                    
                if image_bytes:
                    images.append((image_bytes, mime_type))
            except Exception:
                continue
                
        return images
