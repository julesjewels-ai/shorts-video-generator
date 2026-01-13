import os
import unittest
from pathlib import Path
from dance_loop_gen.utils.prompt_loader import PromptLoader
from dance_loop_gen.config import Config

class TestPromptLoaderSecurity(unittest.TestCase):
    def setUp(self):
        # Create a dummy prompt file
        self.dummy_prompt = "test_prompt.txt"
        self.prompt_content = "This is a test prompt."

        # Ensure prompts directory exists
        os.makedirs(Config.PROMPTS_DIR, exist_ok=True)

        with open(os.path.join(Config.PROMPTS_DIR, self.dummy_prompt), "w") as f:
            f.write(self.prompt_content)

        # Create a secret file outside
        self.secret_file = "secret_test.txt"
        self.secret_content = "SECRET"
        with open(self.secret_file, "w") as f:
            f.write(self.secret_content)

    def tearDown(self):
        # Cleanup
        if os.path.exists(os.path.join(Config.PROMPTS_DIR, self.dummy_prompt)):
            os.remove(os.path.join(Config.PROMPTS_DIR, self.dummy_prompt))
        if os.path.exists(self.secret_file):
            os.remove(self.secret_file)

    def test_load_valid_file(self):
        """Test loading a valid file inside prompts directory."""
        content = PromptLoader.load(self.dummy_prompt)
        self.assertEqual(content, self.prompt_content)

    def test_path_traversal_attack(self):
        """Test that path traversal attempts raise ValueError."""
        # Calculate relative path to secret file from prompts dir
        # prompts dir is ./prompts
        # secret is ./secret_test.txt
        # So ../secret_test.txt

        with self.assertRaises(ValueError) as cm:
            PromptLoader.load(f"../{self.secret_file}")

        self.assertIn("Security event", str(cm.exception))

    def test_absolute_path_attack(self):
        """Test that absolute path attempts raise ValueError."""
        abs_path = os.path.abspath(self.secret_file)
        with self.assertRaises(ValueError) as cm:
            PromptLoader.load(abs_path)

        self.assertIn("Security event", str(cm.exception))

    def test_sibling_path_attack(self):
        """Test that accessing a sibling directory with similar prefix is blocked."""
        # This test ensures `startswith` bug is fixed.
        # prompts dir is ./prompts
        # Create ./prompts_fake
        fake_dir = "prompts_fake"
        os.makedirs(fake_dir, exist_ok=True)
        try:
            with open(os.path.join(fake_dir, "fake.txt"), "w") as f:
                f.write("FAKE")

            # Construct path ../prompts_fake/fake.txt
            # On linux, if we are in root, and PROMPTS_DIR is ./prompts
            # ../prompts_fake/fake.txt is relative to prompts dir?
            # No, load takes filename and does (base_dir / filename).resolve()
            # If filename is ../prompts_fake/fake.txt
            # base_dir is /app/prompts
            # target is /app/prompts_fake/fake.txt
            # string /app/prompts_fake/fake.txt DOES start with /app/prompts if we are not careful about separator

            # Note: /app/prompts_fake starts with /app/prompts only if checking string without trailing slash.
            # pathlib relative_to handles this correctly.

            with self.assertRaises(ValueError) as cm:
                PromptLoader.load("../prompts_fake/fake.txt")

            self.assertIn("Security event", str(cm.exception))

        finally:
            import shutil
            if os.path.exists(fake_dir):
                shutil.rmtree(fake_dir)

    def test_load_optional_valid(self):
        content = PromptLoader.load_optional(self.dummy_prompt)
        self.assertEqual(content, self.prompt_content)

    def test_load_optional_invalid_security(self):
        """Test load_optional returns None on security violation."""
        content = PromptLoader.load_optional(f"../{self.secret_file}")
        self.assertIsNone(content)

if __name__ == "__main__":
    unittest.main()
