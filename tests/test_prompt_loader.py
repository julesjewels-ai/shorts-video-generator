import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure we can import from dance_loop_gen
sys.path.append(os.getcwd())

from dance_loop_gen.utils.prompt_loader import PromptLoader

class TestPromptLoader:
    @patch("dance_loop_gen.utils.prompt_loader.Config")
    def test_load_existing_file(self, mock_config, tmp_path):
        # Setup
        d = tmp_path / "prompts"
        d.mkdir()
        p = d / "test_prompt.txt"
        p.write_text("Hello World", encoding="utf-8")

        # Configure the mock to return the temp directory
        mock_config.PROMPTS_DIR = str(d)

        # Execute
        content = PromptLoader.load("test_prompt.txt")

        # Verify
        assert content == "Hello World"

    @patch("dance_loop_gen.utils.prompt_loader.Config")
    def test_load_non_existent_file(self, mock_config, tmp_path):
        # Setup
        d = tmp_path / "prompts"
        d.mkdir()
        mock_config.PROMPTS_DIR = str(d)

        # Execute & Verify
        with pytest.raises(FileNotFoundError):
            PromptLoader.load("non_existent.txt")

    @patch("dance_loop_gen.utils.prompt_loader.Config")
    def test_load_formatted(self, mock_config, tmp_path):
        # Setup
        d = tmp_path / "prompts"
        d.mkdir()
        p = d / "template.txt"
        p.write_text("Hello {name}", encoding="utf-8")
        mock_config.PROMPTS_DIR = str(d)

        # Execute
        content = PromptLoader.load_formatted("template.txt", name="Ockham")

        # Verify
        assert content == "Hello Ockham"

    @patch("dance_loop_gen.utils.prompt_loader.Config")
    def test_load_multiple_images(self, mock_config, tmp_path):
        # Setup
        d = tmp_path / "prompts"
        d.mkdir()

        # Create dummy images
        (d / "pose_1.png").write_bytes(b"image1")
        (d / "pose_2.jpg").write_bytes(b"image2")
        (d / "pose_10.png").write_bytes(b"image10")
        (d / "other.png").write_bytes(b"other")

        mock_config.PROMPTS_DIR = str(d)

        # Execute
        images = PromptLoader.load_multiple_images("pose")

        # Verify
        # Expected order: pose_1.png, pose_10.png, pose_2.jpg (lexicographical sort)
        assert len(images) == 3

        # Check content and type
        assert images[0][0] == b"image1"
        assert images[0][1] == "image/png"

        assert images[1][0] == b"image10"
        assert images[1][1] == "image/png"

        assert images[2][0] == b"image2"
        assert images[2][1] == "image/jpeg"

    @patch("dance_loop_gen.utils.prompt_loader.Config")
    def test_load_multiple_images_empty_file(self, mock_config, tmp_path):
        # Setup
        d = tmp_path / "prompts"
        d.mkdir()

        # Create empty image
        (d / "pose_1.png").write_bytes(b"")
        (d / "pose_2.png").write_bytes(b"valid")

        mock_config.PROMPTS_DIR = str(d)

        # Execute
        images = PromptLoader.load_multiple_images("pose")

        # Verify
        assert len(images) == 1
        assert images[0][0] == b"valid"
