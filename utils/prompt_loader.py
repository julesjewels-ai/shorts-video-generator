import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

class PromptLoader:
    @staticmethod
    def _safe_join(base_dir: str, *paths: str) -> str:
        """Safely joins paths and ensures the result is within base_dir.

        Args:
            base_dir: The trusted base directory.
            *paths: Path components to join.

        Returns:
            The resolved absolute path as a string.

        Raises:
            ValueError: If the resulting path traverses outside base_dir.
        """
        # Convert to absolute resolved paths
        base_path = Path(base_dir).resolve()

        # Join components and resolve
        unsafe_path = base_path.joinpath(*paths)
        final_path = unsafe_path.resolve()

        # Check if final path is within base path
        try:
            final_path.relative_to(base_path)
        except ValueError:
            raise ValueError(f"Security Alert: Path traversal attempt detected. '{final_path}' is not within '{base_path}'")

        return str(final_path)

    @staticmethod
    def load(filename: str) -> str:
        """Loads a prompt text file from the configured prompts directory."""
        from ..config import Config  # Lazy import to avoid circular dependency
        
        # This will raise ValueError on path traversal, which is the intended security behavior
        path = PromptLoader._safe_join(Config.PROMPTS_DIR, filename)

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
        except (FileNotFoundError, ValueError):
            # Swallow ValueError from safe_join to safely return None on traversal attempts for optional files.
            # While traversal attempts are suspicious, optional loading should not crash the application.
            return None
        except Exception:
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
            path = PromptLoader._safe_join(Config.PROMPTS_DIR, filename)
        except ValueError:
             # Traversal attempt on image load
             return None

        # Check for exact match first
        if not os.path.exists(path):
            # If it's a generic request without extension, try common ones
            base, ext = os.path.splitext(filename)
            if not ext:
                found = False
                for target_ext in [".png", ".jpg", ".jpeg"]:
                    try:
                        # Try to join again safely
                        test_path = PromptLoader._safe_join(Config.PROMPTS_DIR, filename + target_ext)
                        if os.path.exists(test_path):
                            path = test_path
                            found = True
                            break
                    except ValueError:
                        continue
                if not found:
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
            # Glob search is not recursive unless recursive=True is used, so simple *ext is fine.
            # Since we search inside 'directory', if 'directory' is safe, results are safe.
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
        
        # Sanitize pattern to prevent traversal in pattern (e.g. "../secret")
        # Although glob handles paths, ensure pattern is just a filename stem.
        if ".." in pattern or "/" in pattern or "\\" in pattern:
             return []

        # Build search pattern for numbered files
        matching_files = []
        for ext in ["png", "jpg", "jpeg", "jpe"]:
            # We construct the search pattern.
            # Note: glob.glob with absolute path returns absolute paths.
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

            # Additional safety: ensure the found file is indeed in PROMPTS_DIR
            try:
                PromptLoader._safe_join(Config.PROMPTS_DIR, os.path.basename(path))
            except ValueError:
                continue

            try:
                with open(path, "rb") as f:
                    image_bytes = f.read()
                    
                if image_bytes:
                    images.append((image_bytes, mime_type))
            except Exception:
                continue
                
        return images
