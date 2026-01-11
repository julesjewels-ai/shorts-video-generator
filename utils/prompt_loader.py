import os
import mimetypes
from typing import Dict, Any, Optional, Tuple

class PromptLoader:
    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        from ..config import Config  # Lazy import to avoid circular dependency
        
        path = os.path.join(Config.PROMPTS_DIR, filename)
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
        
        path = os.path.join(Config.PROMPTS_DIR, filename)
        
        # Check for exact match first
        if not os.path.exists(path):
            # If it's a generic request without extension, try common ones
            base, ext = os.path.splitext(filename)
            if not ext:
                for target_ext in [".png", ".jpg", ".jpeg"]:
                    test_path = path + target_ext
                    if os.path.exists(test_path):
                        path = test_path
                        break
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
        import glob
        
        # Build search pattern for numbered files
        matching_files = []
        for ext in ["png", "jpg", "jpeg", "jpe"]:
            search_pattern = os.path.join(Config.PROMPTS_DIR, f"{pattern}_*.{ext}")
            matching_files.extend(glob.glob(search_pattern))
        
        if not matching_files:
            return []
        
        # Sort to ensure consistent ordering (1, 2, 3, ...)
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


