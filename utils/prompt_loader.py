import os
import mimetypes
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger()

class PromptLoader:
    @staticmethod
    def _validate_path(path_str: str) -> str:
        """Validates that a path is within the configured prompts directory to prevent traversal.

        Args:
            path_str: The path to validate.

        Returns:
            The resolved absolute path as a string.

        Raises:
            ValueError: If the path is outside the prompts directory.
        """
        from config import Config

        # Resolve both paths to absolute
        base = Path(Config.PROMPTS_DIR).resolve()
        target = Path(path_str).resolve()

        # Check if target is inside base
        # We use relative_to because it strictly checks the hierarchy
        try:
            target.relative_to(base)
        except ValueError:
            logger.error(f"Security event: Path traversal attempt blocked. Target: {target}, Base: {base}")
            raise ValueError(f"Access denied: Path is outside the allowed directory.")

        return str(target)

    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        from config import Config  # Lazy import to avoid circular dependency
        
        path = os.path.join(Config.PROMPTS_DIR, filename)

        # Validate path
        validated_path = PromptLoader._validate_path(path)

        if not os.path.exists(validated_path):
            raise FileNotFoundError(f"Prompt file not found: {validated_path}")
            
        with open(validated_path, "r", encoding="utf-8") as f:
            return f.read().strip()
            
    @staticmethod
    def load_formatted(filename: str, **kwargs: Any) -> str:
        """Loads and formats a prompt with the given keyword arguments."""
        content = PromptLoader.load(filename)
        return content.format(**kwargs)

    @staticmethod
    def load_optional(filename: str) -> Optional[str]:
        """Loads a prompt file, returning None if missing or empty."""
        try:
            content = PromptLoader.load(filename)
            return content if content.strip() else None
        except (FileNotFoundError, ValueError):
            return None

    @staticmethod
    def load_optional_image(filename: str) -> Optional[Tuple[bytes, str]]:
        """Loads an optional image file from the prompts directory."""
        from config import Config
        
        candidates = []
        base_path = os.path.join(Config.PROMPTS_DIR, filename)
        
        # If filename has extension, check it first
        _, ext = os.path.splitext(filename)
        if ext:
            candidates.append(base_path)
        else:
            # Try extensions
            for target_ext in [".png", ".jpg", ".jpeg"]:
                candidates.append(base_path + target_ext)

        for path in candidates:
            try:
                # Validate BEFORE checking existence to prevent enumeration
                validated_path = PromptLoader._validate_path(path)

                if os.path.exists(validated_path):
                    # Determine MIME type
                    mime_type, _ = mimetypes.guess_type(validated_path)
                    if mime_type and mime_type.startswith('image/'):
                        with open(validated_path, "rb") as f:
                            image_bytes = f.read()
                        if image_bytes:
                            return (image_bytes, mime_type)
            except ValueError:
                continue

        return None

    @staticmethod
    def load_images_from_directory(directory: str) -> list:
        """Loads all image files from a specific directory."""
        try:
            validated_dir = PromptLoader._validate_path(directory)
        except ValueError:
             return []

        if not os.path.exists(validated_dir) or not os.path.isdir(validated_dir):
            return []
            
        matching_files = []
        for ext in [".png", ".jpg", ".jpeg", ".jpe", ".webp"]:
            import glob
            # We use validated_dir which is safe
            search_pattern = os.path.join(validated_dir, f"*{ext}")
            matching_files.extend(glob.glob(search_pattern))
            search_pattern_upper = os.path.join(validated_dir, f"*{ext.upper()}")
            matching_files.extend(glob.glob(search_pattern_upper))
            
        if not matching_files:
            return []
            
        matching_files.sort()
        
        images = []
        for path in matching_files:
            mime_type, _ = mimetypes.guess_type(path)
            if not mime_type or not mime_type.startswith('image/'):
                continue
                
            try:
                # Double check each file
                PromptLoader._validate_path(path)

                with open(path, "rb") as f:
                    image_bytes = f.read()
                    
                if image_bytes:
                    images.append((image_bytes, mime_type))
            except Exception:
                continue
                
        return images

    @staticmethod
    def load_multiple_images(pattern: str) -> list:
        """Loads multiple image files matching a pattern from the prompts directory."""
        from config import Config
        import glob
        
        matching_files = []
        for ext in ["png", "jpg", "jpeg", "jpe"]:
            search_pattern = os.path.join(Config.PROMPTS_DIR, f"{pattern}_*.{ext}")
            matching_files.extend(glob.glob(search_pattern))
        
        if not matching_files:
            return []
        
        matching_files.sort()
        
        images = []
        for path in matching_files:
            try:
                PromptLoader._validate_path(path)
            except ValueError:
                continue

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
