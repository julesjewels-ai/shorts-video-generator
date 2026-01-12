
import pytest
from unittest.mock import MagicMock, patch
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.core.models import VideoPlan, Scene
from google.genai import types

@pytest.fixture
def mock_client():
    client = MagicMock()
    return client

@pytest.fixture
def service(mock_client):
    # Mock PromptLoader to avoid file system issues during initialization if any
    with patch('dance_loop_gen.services.cinematographer.PromptLoader') as mock_loader:
         # Setup mock returns for PromptLoader
        mock_loader.load_multiple_images.return_value = []
        mock_loader.load_optional_image.return_value = None

        service = CinematographerService(mock_client)
        return service

@pytest.fixture
def sample_plan():
    scenes = [
        Scene(
            scene_number=1,
            action_description="Action 1",
            audio_prompt="Audio 1",
            start_pose_description="Pose A",
            end_pose_description="Pose B"
        ),
        Scene(
            scene_number=2,
            action_description="Action 2",
            audio_prompt="Audio 2",
            start_pose_description="Pose B",
            end_pose_description="Pose C"
        ),
        Scene(
            scene_number=3,
            action_description="Action 3",
            audio_prompt="Audio 3",
            start_pose_description="Pose C",
            end_pose_description="Pose D"
        ),
        Scene(
            scene_number=4,
            action_description="Action 4",
            audio_prompt="Audio 4",
            start_pose_description="Pose D",
            end_pose_description="Pose A"
        ),
    ]
    return VideoPlan(
        title="Test Plan",
        description="A test plan description",
        backend_tags=["dance", "test"],
        setting_desc="A studio",
        character_leader_desc="Leader",
        character_follower_desc="Follower",
        scenes=scenes
    )

def test_generate_assets_calls(service, sample_plan, mock_client):
    # Mock PromptLoader.load_formatted to return dummy prompts
    with patch('dance_loop_gen.services.cinematographer.PromptLoader.load_formatted', side_effect=lambda template, **kwargs: f"Prompt for {template}"):
        # Mock _save_image to avoid file system writes
        service._save_image = MagicMock(side_effect=lambda part, filename: f"/tmp/{filename}")

        # Create a real Blob for inline_data
        blob = types.Blob(mime_type="image/png", data=b"fake_image_data")

        # Create a real Part with inline_data
        real_part = types.Part(inline_data=blob)

        # Mock API responses using a real Part in a real Content-like structure if needed, or just a mock that has parts attribute which is a list of real Parts.
        mock_response = MagicMock()
        mock_response.parts = [real_part]

        mock_client.models.generate_content.return_value = mock_response

        assets = service.generate_assets(sample_plan, output_dir="/tmp/test_output")

        assert len(assets) == 4
        assert assets['A'] == "/tmp/keyframe_A.png"
        assert assets['B'] == "/tmp/keyframe_B.png"
        assert assets['C'] == "/tmp/keyframe_C.png"
        assert assets['D'] == "/tmp/keyframe_D.png"

        # Verify API calls
        assert mock_client.models.generate_content.call_count == 4
