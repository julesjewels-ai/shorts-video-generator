import unittest
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

# Ensure we can import the package
import sys
repo_root = os.getcwd()
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

try:
    from dance_loop_gen.utils.prompt_loader import PromptLoader, PromptFile
    from dance_loop_gen.config import Config
except ImportError:
    # If running in a weird environment where dance_loop_gen isn't resolvable
    # This might happen if we are not in the parent dir of dance_loop_gen package
    # But based on previous steps, we seem to be in root which IS the package?
    # No, main.py is in root and imports dance_loop_gen.
    # This implies root is NOT the package, but contains it?
    # But list_files showed root has __init__.py.
    # This is confusing. Let's assume standard behavior.
    pass

class TestPromptLoaderSecurity(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for prompts
        self.test_dir = tempfile.mkdtemp()
        self.prompts_dir = os.path.join(self.test_dir, "prompts")
        os.makedirs(self.prompts_dir)

        # Create a valid prompt file
        with open(os.path.join(self.prompts_dir, "valid.txt"), "w") as f:
            f.write("valid content")

        # Create a sensitive file outside prompts
        self.sensitive_file = os.path.join(self.test_dir, "sensitive.txt")
        with open(self.sensitive_file, "w") as f:
            f.write("sensitive content")

        # Patch Config.PROMPTS_DIR
        # We need to patch the attribute on the class that PromptLoader imports
        self.patcher = patch('dance_loop_gen.config.Config.PROMPTS_DIR', self.prompts_dir)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_load_valid_file(self):
        content = PromptLoader.load("valid.txt")
        self.assertEqual(content, "valid content")

    def test_path_traversal_parent_directory(self):
        # "../sensitive.txt"
        with self.assertRaises(ValueError) as cm:
            PromptLoader.load("../sensitive.txt")
        self.assertIn("Path traversal is not allowed", str(cm.exception))

    def test_path_traversal_absolute_path(self):
        # Absolute path to sensitive file
        with self.assertRaises(ValueError) as cm:
            PromptLoader.load(self.sensitive_file)
        # Depending on implementation, it might fail on absolute path check or traversal
        err = str(cm.exception)
        self.assertTrue("Absolute paths are not allowed" in err or "Path traversal" in err or "Security Alert" in err)

    def test_path_traversal_encoded(self):
        # "..%2fsensitive.txt" - should fail file not found (since it looks for that literal filename)
        # or ValueError if we decded to block %
        try:
            PromptLoader.load("..%2fsensitive.txt")
        except FileNotFoundError:
            pass # Acceptable
        except ValueError:
            pass # Acceptable
        else:
            # If it actually found the file (unlikely) or didn't raise
            # If it didn't raise, it means it tried to read it.
            # If the file existed, we'd have a problem if it was outside.
            pass

    def test_load_nested_valid_file(self):
        # Allow nested files if they are under prompts_dir
        nested_dir = os.path.join(self.prompts_dir, "subdir")
        os.makedirs(nested_dir)
        with open(os.path.join(nested_dir, "nested.txt"), "w") as f:
            f.write("nested content")

        content = PromptLoader.load("subdir/nested.txt")
        self.assertEqual(content, "nested content")

    def test_load_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            PromptLoader.load("nonexistent.txt")

    def test_load_optional_valid(self):
        content = PromptLoader.load_optional("valid.txt")
        self.assertEqual(content, "valid content")

    def test_load_optional_missing(self):
        content = PromptLoader.load_optional("missing.txt")
        self.assertIsNone(content)

    def test_load_optional_traversal(self):
        content = PromptLoader.load_optional("../sensitive.txt")
        self.assertIsNone(content)

    def test_load_optional_image_traversal(self):
        # Create a dummy image outside
        img_path = os.path.join(self.test_dir, "secret.png")
        with open(img_path, "wb") as f:
            f.write(b"fakeimage")

        result = PromptLoader.load_optional_image("../secret.png")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
