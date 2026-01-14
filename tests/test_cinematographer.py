import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# Mock google.genai and google.genai.types before importing service
sys.modules['google'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()

from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.core.models import VideoPlan, Scene

class TestCinematographerService:
    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        # Mock response for generate_content
        mock_response = MagicMock()

        # Mock parts for the response
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.data = b"fake_image_data"
        mock_part.inline_data.mime_type = "image/png"
        mock_response.parts = [mock_part]

        client.models.generate_content.return_value = mock_response
        return client

    @pytest.fixture
    def mock_prompt_loader(self):
        with patch('dance_loop_gen.services.cinematographer.PromptLoader') as mock:
            # Setup default returns
            mock.load_images_from_directory.return_value = []
            mock.load_multiple_images.return_value = []
            mock.load_optional_image.return_value = None
            mock.load_formatted.return_value = "Mock Prompt"
            yield mock

    @pytest.fixture
    def mock_config(self):
        with patch('dance_loop_gen.services.cinematographer.Config') as mock:
            mock.OUTPUT_DIR = "/tmp/mock_output"
            mock.REFERENCE_IMAGES_DIR = "/tmp/mock_ref"
            mock.SCENE_VARIETY = 5
            mock.MODEL_NAME_IMAGE = "mock-model"
            yield mock

    @pytest.fixture
    def service(self, mock_client, mock_prompt_loader, mock_config):
        return CinematographerService(mock_client)

    def test_generate_assets_flow(self, service, mock_client):
        # Setup VideoPlan
        plan = VideoPlan(
            title="Test Video",
            description="Test Description",
            setting_desc="Test Setting",
            character_leader_desc="Leader",
            character_follower_desc="Follower",
            scenes=[
                Scene(scene_number=1, start_pose_description="Pose A", end_pose_description="End Pose A", action_description="Action A", audio_prompt="Audio A"),
                Scene(scene_number=2, start_pose_description="Pose B", end_pose_description="End Pose B", action_description="Action B", audio_prompt="Audio B"),
                Scene(scene_number=3, start_pose_description="Pose C", end_pose_description="End Pose C", action_description="Action C", audio_prompt="Audio C")
            ],
            backend_tags=["tag1"]
        )

        # Mock file writing
        with patch("builtins.open", mock_open()) as mock_file:
            assets = service.generate_assets(plan)

        # Verification
        assert assets['A'] is not None
        assert assets['B'] is not None
        assert assets['C'] is not None

        # Check API calls
        # Keyframe A + Keyframe B + Keyframe C = 3 calls
        assert mock_client.models.generate_content.call_count == 3

        # Verify first call (Keyframe A) uses simple content or with ref pose
        # Verify subsequent calls use history

    def test_reference_pose_loading(self, mock_client, mock_prompt_loader, mock_config):
        # Test that it tries to load from directory first
        mock_prompt_loader.load_images_from_directory.return_value = [(b"img1", "image/png")]

        service = CinematographerService(mock_client)
        assert len(service.reference_poses) == 1

        # Check call arguments
        mock_prompt_loader.load_images_from_directory.assert_called_with(mock_config.REFERENCE_IMAGES_DIR)
