import unittest
import os
from pathlib import Path
from dance_loop_gen.utils.prompt_loader import PromptLoader
from dance_loop_gen.config import Config

class TestPathTraversal(unittest.TestCase):
    def setUp(self):
        # Create a dummy secret file in the root directory
        self.secret_file = Path("secret.txt").resolve()
        self.secret_file.write_text("SUPER_SECRET_DATA")

        # Ensure prompts dir exists
        self.prompts_dir = Path(Config.PROMPTS_DIR).resolve()
        self.prompts_dir.mkdir(parents=True, exist_ok=True)

        # Create a valid prompt file
        self.valid_prompt = self.prompts_dir / "valid.txt"
        self.valid_prompt.write_text("safe content")

    def tearDown(self):
        if self.secret_file.exists():
            self.secret_file.unlink()
        if self.valid_prompt.exists():
            self.valid_prompt.unlink()

    def test_path_traversal_load(self):
        # Calculate path to secret.txt relative to PROMPTS_DIR
        try:
            rel_path = os.path.relpath(self.secret_file, self.prompts_dir)
        except ValueError:
            rel_path = "../../secret.txt"

        print(f"DEBUG: Testing load with path: {rel_path}")

        # Now this SHOULD raise ValueError
        with self.assertRaises(ValueError) as cm:
            PromptLoader.load(rel_path)

        self.assertIn("Security Alert: Path traversal attempt detected", str(cm.exception))

    def test_path_traversal_optional(self):
        try:
            rel_path = os.path.relpath(self.secret_file, self.prompts_dir)
        except ValueError:
            rel_path = "../../secret.txt"

        # Optional load should simply return None on traversal attempt (handled in load_optional)
        content = PromptLoader.load_optional(rel_path)
        self.assertIsNone(content, "Optional load should return None for traversal attempt")

    def test_valid_load(self):
        content = PromptLoader.load("valid.txt")
        self.assertEqual(content, "safe content")

if __name__ == "__main__":
    unittest.main()
