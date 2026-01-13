import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class PromptLoader:
    @staticmethod
    def _get_safe_path(filename: str) -> Path:
        """
        Resolves the filename within the prompts directory and ensures
        it doesn't traverse outside of it.
        """
        from ..config import Config  # Lazy import to avoid circular dependency
        from ..utils.logger import setup_logger # Lazy import
        
        logger = setup_logger()

        base_dir = Path(Config.PROMPTS_DIR).resolve()

        if os.path.isabs(filename):
             msg = f"Security event: Absolute path attempt blocked: {filename}"
             logger.error(msg)
             raise ValueError(msg)

        target_path = (base_dir / filename).resolve()

        # Security check: Ensure the resolved path is relative to base directory
        # Using is_relative_to (Python 3.9+)
        try:
            target_path.relative_to(base_dir)
        except ValueError:
            msg = f"Security event: Path traversal attempt blocked: {filename} (resolved to {target_path})"
            logger.error(msg)
            raise ValueError(msg)

        return target_path

    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        try:
            path = PromptLoader._get_safe_path(filename)
        except ValueError as e:
            # Re-raise as ValueError or handle?
            # Original code raised FileNotFoundError if not found.
            # Here we might be raising ValueError for security.
            raise e

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
            content = PromptLoader.load(filename)
            return content if content.strip() else None
        except (FileNotFoundError, ValueError):
            # ValueError is raised for security violations, which are logged.
            # We return None to fail gracefully in the application flow,
            # but the security event is already logged.
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
        try:
            path = PromptLoader._get_safe_path(filename)
        except ValueError:
            return None
        
        # Check for exact match first
        if not path.exists():
            # If it's a generic request without extension, try common ones
            base, ext = os.path.splitext(filename)
            if not ext:
                for target_ext in [".png", ".jpg", ".jpeg"]:
                    try:
                        test_path = PromptLoader._get_safe_path(filename + target_ext)
                        if test_path.exists():
                            path = test_path
                            break
                    except ValueError:
                        continue
                else:
                    return None
            else:
                return None
            
        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(path)
        if not mime_type or not mime_type.startswith('image/'):
            return None
            
        with open(path, "rb") as f:
            image_bytes = f.read()
            
        return (image_bytes, mime_type) if image_bytes else None

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
        from ..utils.logger import setup_logger
        import glob
        
        logger = setup_logger()

        # Security check: pattern should not contain directory separators
        if os.sep in pattern or (os.altsep and os.altsep in pattern):
             msg = f"Security event: Invalid pattern containing path separators: {pattern}"
             logger.error(msg)
             raise ValueError(msg)

        # Build search pattern for numbered files
        matching_files = []
        base_dir = Path(Config.PROMPTS_DIR).resolve()

        for ext in ["png", "jpg", "jpeg", "jpe"]:
            # We construct the search pattern relative to base_dir
            search_pattern = base_dir / f"{pattern}_*.{ext}"
            matching_files.extend(glob.glob(str(search_pattern)))
        
        if not matching_files:
            return []
        
        # Sort to ensure consistent ordering (1, 2, 3, ...)
        matching_files.sort()
        
        images = []
        for path_str in matching_files:
            # Double check that the found file is indeed in base_dir
            # (glob shouldn't return outside files unless pattern has .., which we checked)

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(path_str)
            if not mime_type or not mime_type.startswith('image/'):
                continue
                
            try:
                with open(path_str, "rb") as f:
                    image_bytes = f.read()
                    
                if image_bytes:
                    images.append((image_bytes, mime_type))
            except Exception:
                continue
                
        return images
