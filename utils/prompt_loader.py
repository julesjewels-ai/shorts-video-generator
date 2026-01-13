import os
import mimetypes
from typing import Dict, Any, Optional, Tuple
from ..config import Config

class PromptLoader:
    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
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
        """Loads multiple image files matching a pattern from the prompts directory."""
        from pathlib import Path
        
        prompts_dir = Path(Config.PROMPTS_DIR)
        images = []

        # Find all matching files (sorted for consistency)
        # Using sorted ensures 1 comes before 2, but '10' comes before '2'.
        # Standard glob behavior in original code also had this dictionary sort issue.
        # Strict Ockham: preserve behavior while simplifying.
        files = sorted([
            p for p in prompts_dir.glob(f"{pattern}_*")
            if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.jpe'}
        ])

        for path in files:
            mime_type, _ = mimetypes.guess_type(path)
            if mime_type and mime_type.startswith('image/'):
                try:
                    content = path.read_bytes()
                    if content:
                        images.append((content, mime_type))
                except Exception:
                    continue
                    
        return images


