import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

class PromptLoader:
    @staticmethod
    def _validate_path(path_str: str) -> Path:
        """
        Validates that the path resolves to a location inside Config.PROMPTS_DIR.
        Prevents Path Traversal attacks.

        Args:
            path_str: The file path (relative or absolute).

        Returns:
            The resolved Path object if valid.

        Raises:
            ValueError: If the path is outside the allowed directory.
        """
        from config import Config
        base_dir = Path(Config.PROMPTS_DIR).resolve()

        path = Path(path_str)

        # Handle absolute vs relative paths
        if path.is_absolute():
            full_path = path.resolve()
        else:
            # Join with base_dir if relative
            full_path = (base_dir / path_str).resolve()

        # Security check: Ensure the resolved path is within base_dir
        # We check if base_dir is a parent of full_path, or if they are the same directory
        if base_dir != full_path and base_dir not in full_path.parents:
            raise ValueError(f"Security violation: Path {path_str} is outside the prompts directory.")

        return full_path

    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        
        try:
            path = PromptLoader._validate_path(filename)
        except ValueError as e:
            # Log security event? For now, just raise to stop execution.
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
        """Loads a prompt file, returning None if missing or empty."""
        try:
            # We use load() which includes validation
            content = PromptLoader.load(filename)
            return content if content.strip() else None
        except (FileNotFoundError, ValueError):
            # Return None on missing file OR security violation (fail safe for optional files)
            return None

    @staticmethod
    def load_optional_image(filename: str) -> Optional[Tuple[bytes, str]]:
        """Loads an optional image file from the prompts directory."""
        try:
            path = PromptLoader._validate_path(filename)
        except ValueError:
            return None
        
        # Check for exact match first
        if not path.exists():
            # If it's a generic request without extension, try common ones
            # We must validate these generated paths too, though they should be safe if filename was safe (only adding extension)
            if not path.suffix:
                for target_ext in [".png", ".jpg", ".jpeg"]:
                    test_path = path.with_suffix(target_ext)
                    if test_path.exists():
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
    def load_images_from_directory(directory: str) -> list:
        """Loads all image files from a specific directory.
        
        Args:
            directory: Path to the directory containing images.
            
        Returns:
            List of tuples of (image_bytes, mime_type), sorted by filename.
        """
        try:
            dir_path = PromptLoader._validate_path(directory)
        except ValueError:
            return []

        if not dir_path.exists() or not dir_path.is_dir():
            return []
            
        matching_files = []
        for ext in [".png", ".jpg", ".jpeg", ".jpe", ".webp"]:
            # Use pathlib glob
            matching_files.extend(dir_path.glob(f"*{ext}"))
            matching_files.extend(dir_path.glob(f"*{ext.upper()}"))
            
        if not matching_files:
            return []
            
        # Sort to ensure consistent ordering (Path objects sortable)
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
        """Loads multiple image files matching a pattern from the prompts directory."""
        from config import Config
        
        # Security check on the pattern prefix
        try:
            # Check if pattern attempts traversal
            PromptLoader._validate_path(pattern)
        except ValueError:
            return []

        # Safe to proceed with globbing in PROMPTS_DIR
        base_dir = Path(Config.PROMPTS_DIR)
        
        matching_files = []
        for ext in ["png", "jpg", "jpeg", "jpe"]:
             # Glob supports recursive ** but we only want flat list?
             # Original code: os.path.join(Config.PROMPTS_DIR, f"{pattern}_*.{ext}")
             # This means it searches for files starting with pattern_ in PROMPTS_DIR.
             # If pattern contains slashes, it searches in subdirs.

             # Use glob on the base_dir
             search_pattern = f"{pattern}_*.{ext}"
             matching_files.extend(base_dir.glob(search_pattern))
        
        if not matching_files:
            return []
        
        matching_files.sort()
        
        images = []
        for path in matching_files:
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
