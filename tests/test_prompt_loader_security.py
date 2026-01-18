import unittest
import os
import shutil
from pathlib import Path
from dance_loop_gen.utils.prompt_loader import PromptLoader
from dance_loop_gen.config import Config

class TestPromptLoaderSecurity(unittest.TestCase):
    def setUp(self):
        # Create a dummy file in prompts dir
        self.prompts_dir = Path(Config.PROMPTS_DIR).resolve()
        os.makedirs(self.prompts_dir, exist_ok=True)

        self.safe_file = self.prompts_dir / "safe.txt"
        with open(self.safe_file, "w") as f:
            f.write("safe content")

        # Create a file outside prompts dir
        self.outside_dir = self.prompts_dir.parent / "temp_outside"
        os.makedirs(self.outside_dir, exist_ok=True)
        self.secret_file = self.outside_dir / "secret.txt"
        with open(self.secret_file, "w") as f:
            f.write("secret content")

    def tearDown(self):
        if self.safe_file.exists():
            os.remove(self.safe_file)
        if self.secret_file.exists():
            os.remove(self.secret_file)
        if self.outside_dir.exists():
            shutil.rmtree(self.outside_dir)

    def test_load_safe_path(self):
        content = PromptLoader.load("safe.txt")
        self.assertEqual(content, "safe content")

    def test_load_path_traversal(self):
        # Attempt to access the secret file using relative path
        rel_path = f"../temp_outside/{self.secret_file.name}"

        with self.assertRaises(ValueError) as context:
            PromptLoader.load(rel_path)

        self.assertIn("Security violation", str(context.exception))

    def test_load_absolute_path_outside(self):
        # Attempt to access using absolute path
        with self.assertRaises(ValueError) as context:
            PromptLoader.load(str(self.secret_file.resolve()))

        self.assertIn("Security violation", str(context.exception))

    def test_load_optional_traversal(self):
        rel_path = f"../temp_outside/{self.secret_file.name}"
        # load_optional catches ValueError and returns None
        result = PromptLoader.load_optional(rel_path)
        self.assertIsNone(result)

    def test_load_multiple_images_traversal(self):
        # Pattern checking
        rel_pattern = "../temp_outside/secret"
        result = PromptLoader.load_multiple_images(rel_pattern)
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
