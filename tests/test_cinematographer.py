import os
import pytest
from unittest.mock import MagicMock, patch
from services.cinematographer import CinematographerService
from core.models import VideoPlan
from google.genai import types

class TestCinematographerService:

    @patch("services.cinematographer.PromptLoader")
    @patch("services.cinematographer.os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_generate_assets(self, mock_open, mock_makedirs, mock_prompt_loader, mock_genai_client, mock_plan):
        # Setup mocks
        mock_prompt_loader.load_images_from_directory.return_value = []
        mock_prompt_loader.load_multiple_images.return_value = []
        mock_prompt_loader.load_optional_image.return_value = None
        mock_prompt_loader.load_formatted.return_value = "Mock Prompt"

        service = CinematographerService(mock_genai_client)

        # Override save_image to avoid actual file writing logic which is complex to mock perfectly with open
        # We can mock _save_image instead since we are testing the orchestration
        with patch.object(service, '_save_image', return_value="/tmp/mock_image.png") as mock_save:
            assets = service.generate_assets(mock_plan, output_dir="/tmp/output")

            assert assets['A'] == "/tmp/mock_image.png"
            assert assets['B'] == "/tmp/mock_image.png"
            assert len(assets) == 2

            # Verify Keyframe A call
            assert mock_genai_client.models.generate_content.call_count == 2

            # Verify first call (Keyframe A)
            call_args_list = mock_genai_client.models.generate_content.call_args_list
            call_a = call_args_list[0]
            # Verify it uses contents_a (string or list)
            assert "contents" in call_a.kwargs

            # Verify second call (Keyframe B)
            call_b = call_args_list[1]
            # Verify it passes history
            assert isinstance(call_b.kwargs['contents'], list)
            # The history should have user, model, user messages
            history = call_b.kwargs['contents']
            # Depending on implementation details, check length
            # A prompt + response parts + B prompt = 3 items in list
            assert len(history) == 3

    @patch("services.cinematographer.PromptLoader")
    def test_build_variety_instruction(self, mock_prompt_loader, mock_genai_client):
        service = CinematographerService(mock_genai_client)

        instr_0 = service._build_variety_instruction(0)
        assert "EXACTLY the same" in instr_0

        instr_10 = service._build_variety_instruction(10)
        assert "Dramatic scene variation" in instr_10
