import unittest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from utils.prompt_loader import PromptLoader

class TestPromptLoader(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for prompts
        self.test_dir = tempfile.mkdtemp()
        self.prompts_dir = os.path.join(self.test_dir, "prompts")
        os.makedirs(self.prompts_dir)

        # Create a valid prompt file
        with open(os.path.join(self.prompts_dir, "test_prompt.txt"), "w") as f:
            f.write("Valid content")

        # Create a file outside prompts dir
        with open(os.path.join(self.test_dir, "secret.txt"), "w") as f:
            f.write("Secret content")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_load_valid_file(self):
        """Test loading a valid file from prompts directory."""
        with patch('config.Config.PROMPTS_DIR', self.prompts_dir):
            content = PromptLoader.load("test_prompt.txt")
            self.assertEqual(content, "Valid content")

    def test_path_traversal_parent_dir(self):
        """Test that accessing parent directory raises ValueError."""
        with patch('config.Config.PROMPTS_DIR', self.prompts_dir):
            with self.assertRaises(ValueError):
                PromptLoader.load("../secret.txt")

    def test_path_traversal_absolute_path(self):
        """Test that accessing absolute path outside prompts raises ValueError."""
        abs_path = os.path.join(self.test_dir, "secret.txt")
        with patch('config.Config.PROMPTS_DIR', self.prompts_dir):
             with self.assertRaises(ValueError):
                PromptLoader.load(abs_path)

    def test_load_optional_image_traversal(self):
        """Test load_optional_image with traversal returns None."""
        with patch('config.Config.PROMPTS_DIR', self.prompts_dir):
            # Should return None and log error
            result = PromptLoader.load_optional_image("../secret.txt")
            self.assertIsNone(result)

    def test_load_optional_traversal(self):
        """Test load_optional with traversal returns None."""
        with patch('config.Config.PROMPTS_DIR', self.prompts_dir):
            result = PromptLoader.load_optional("../secret.txt")
            self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
