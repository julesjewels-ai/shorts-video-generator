import pytest
from unittest.mock import MagicMock, patch
from google.genai import types
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.core.models import VideoPlan, Scene

class MockInlineData:
    def __init__(self, data, mime_type):
        self.data = data
        self.mime_type = mime_type

class MockPart:
    def __init__(self, inline_data=None, text=None):
        self.inline_data = inline_data
        self.text = text

class MockResponse:
    def __init__(self, parts):
        self.parts = parts

@pytest.fixture
def mock_client():
    client = MagicMock()
    # Mock the generate_content method to return a response with an image part
    mock_image_data = b"fake_image_bytes"
    mock_part = MockPart(inline_data=MockInlineData(mock_image_data, "image/png"))
    client.models.generate_content.return_value = MockResponse([mock_part])
    return client

@pytest.fixture
def video_plan():
    return VideoPlan(
        title="Test Plan",
        description="A test plan description",
        backend_tags=["test", "dance"],
        setting_desc="A beautiful dance studio",
        character_leader_desc="Leader",
        character_follower_desc="Follower",
        scenes=[
            Scene(
                scene_number=1,
                action_description="Leader spins follower",
                audio_prompt="Music 120bpm",
                start_pose_description="Pose A",
                end_pose_description="Pose B"
            ),
            Scene(
                scene_number=2,
                action_description="Follower dips",
                audio_prompt="Music 120bpm",
                start_pose_description="Pose B",
                end_pose_description="Pose C"
            ),
        ]
    )

@patch("dance_loop_gen.services.cinematographer.PromptLoader")
@patch("dance_loop_gen.services.cinematographer.Config")
def test_generate_assets(mock_config, mock_prompt_loader, mock_client, video_plan, tmp_path):
    # Setup mocks
    mock_config.OUTPUT_DIR = str(tmp_path)
    mock_config.SCENE_VARIETY = 5
    mock_config.MODEL_NAME_IMAGE = "gemini-pro-vision"

    mock_prompt_loader.load_multiple_images.return_value = []
    mock_prompt_loader.load_optional_image.return_value = None
    mock_prompt_loader.load_formatted.return_value = "Test Prompt"

    service = CinematographerService(mock_client)
    # Override output_dir with tmp_path for test isolation
    service.output_dir = str(tmp_path)

    assets = service.generate_assets(video_plan)

    assert "A" in assets
    assert "B" in assets
    assert assets["A"].endswith("keyframe_A.png")
    assert assets["B"].endswith("keyframe_B.png")

    # Verify generate_content was called twice (once for A, once for B)
    assert mock_client.models.generate_content.call_count == 2
