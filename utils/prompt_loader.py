import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class PromptLoader:
    @staticmethod
    def _validate_path(filename: str, base_dir: str) -> str:
        """Validates that the filename resolves to a path within base_dir.

        Args:
            filename: The relative filename or path.
            base_dir: The trusted base directory.

        Returns:
            The resolved absolute path as a string.

        Raises:
            ValueError: If path traversal is detected.
        """
        base_path = Path(base_dir).resolve()
        target_path = (base_path / filename).resolve()

        # Ensure the resolved path is relative to the base path
        try:
            target_path.relative_to(base_path)
        except ValueError:
            raise ValueError(f"Security violation: Path traversal detected for '{filename}'")

        return str(target_path)

    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        from ..config import Config  # Lazy import to avoid circular dependency
        
        path = PromptLoader._validate_path(filename, Config.PROMPTS_DIR)

        if not os.path.exists(path):
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
        except FileNotFoundError:
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
        from ..config import Config  # Lazy import to avoid circular dependency
        
        try:
            path = PromptLoader._validate_path(filename, Config.PROMPTS_DIR)
        except ValueError:
            return None
        
        # Check for exact match first
        if not os.path.exists(path):
            # If it's a generic request without extension, try common ones
            base, ext = os.path.splitext(filename)
            if not ext:
                for target_ext in [".png", ".jpg", ".jpeg"]:
                    # We need to validate these constructed paths too, though they should be safe if base is safe
                    try:
                        test_path = PromptLoader._validate_path(filename + target_ext, Config.PROMPTS_DIR)
                        if os.path.exists(test_path):
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
    def load_images_from_directory(directory: str) -> list:
        """Loads all image files from a specific directory.
        
        Args:
            directory: Path to the directory containing images.
            
        Returns:
            List of tuples of (image_bytes, mime_type), sorted by filename.
            Empty list if no matching files found or directory doesn't exist.
        """
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return []
            
        matching_files = []
        for ext in [".png", ".jpg", ".jpeg", ".jpe", ".webp"]:
            import glob
            search_pattern = os.path.join(directory, f"*{ext}")
            matching_files.extend(glob.glob(search_pattern))
            # Also try uppercase extensions
            search_pattern_upper = os.path.join(directory, f"*{ext.upper()}")
            matching_files.extend(glob.glob(search_pattern_upper))
            
        if not matching_files:
            return []
            
        # Sort to ensure consistent ordering
        matching_files.sort()
        
        images = []
        for path in matching_files:
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
        
        # Security: Prevent path traversal in pattern
        if ".." in pattern or "/" in pattern or "\\" in pattern:
             # Just return empty list for invalid patterns rather than raising error to avoid breaking flows
             return []

        # Build search pattern for numbered files
        matching_files = []
        for ext in ["png", "jpg", "jpeg", "jpe"]:
            # We construct the pattern safely now
            search_pattern = os.path.join(Config.PROMPTS_DIR, f"{pattern}_*.{ext}")
            matching_files.extend(glob.glob(search_pattern))
        
        if not matching_files:
            return []
        
        # Sort to ensure consistent ordering (1, 2, 3, ...)
        matching_files.sort()
        
        images = []
        for path in matching_files:
            # Validate that the found file is indeed in the prompts directory (defense in depth)
            try:
                PromptLoader._validate_path(os.path.basename(path), Config.PROMPTS_DIR)
            except ValueError:
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


