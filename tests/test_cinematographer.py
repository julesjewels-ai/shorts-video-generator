import pytest
from unittest.mock import MagicMock, patch
import os
from google.genai import types
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.core.models import VideoPlan, Scene
import base64

@pytest.fixture
def mock_client():
    client = MagicMock()
    return client

@pytest.fixture
def sample_plan():
    scenes = [
        Scene(
            scene_number=1,
            action_description="Action 1",
            audio_prompt="Audio 1",
            start_pose_description="Start Pose 1",
            end_pose_description="End Pose 1"
        ),
        Scene(
            scene_number=2,
            action_description="Action 2",
            audio_prompt="Audio 2",
            start_pose_description="Start Pose 2",
            end_pose_description="End Pose 2"
        ),
        Scene(
            scene_number=3,
            action_description="Action 3",
            audio_prompt="Audio 3",
            start_pose_description="Start Pose 3",
            end_pose_description="End Pose 3"
        )
    ]
    return VideoPlan(
        title="Test Video",
        description="Test Description",
        backend_tags=["tag1", "tag2"],
        character_leader_desc="Leader",
        character_follower_desc="Follower",
        setting_desc="Setting",
        scenes=scenes
    )

@pytest.fixture
def mock_prompt_loader():
    with patch("dance_loop_gen.services.cinematographer.PromptLoader") as mock:
        mock.load_images_from_directory.return_value = []
        mock.load_multiple_images.return_value = []
        mock.load_optional_image.return_value = None
        mock.load_formatted.return_value = "Test Prompt"
        yield mock

@pytest.fixture
def mock_config(tmp_path):
    with patch("dance_loop_gen.services.cinematographer.Config") as mock:
        mock.OUTPUT_DIR = str(tmp_path)
        mock.SCENE_VARIETY = 5
        mock.MODEL_NAME_IMAGE = "imagen-3.0-generate-001"
        mock.REFERENCE_IMAGES_DIR = "mock_ref_dir"
        yield mock

def test_generate_assets(mock_client, sample_plan, mock_prompt_loader, mock_config, tmp_path):
    # Create valid response objects using types
    fake_image_data = base64.b64encode(b"fake_image_data").decode('utf-8')

    # We need to construct types.GenerateContentResponse
    # But since we can't easily construct the full complex object if the SDK doesn't expose a simple constructor,
    # we can try to mock the response object but make sure 'parts' contains valid types.Part objects

    # However, the code does:
    # part_a = [p for p in response_a.parts if p.inline_data][0]
    # And later:
    # previous_response_parts = response.parts
    # types.Content(role="model", parts=previous_response_parts)

    # So the parts need to be valid to be passed into types.Content

    part = types.Part(
        inline_data=types.Blob(
            mime_type="image/png",
            data=b"fake_image_data"
        )
    )

    # Mock the response object to have .parts attribute
    mock_response = MagicMock()
    mock_response.parts = [part]

    mock_client.models.generate_content.return_value = mock_response

    service = CinematographerService(mock_client)

    # Run the method
    assets = service.generate_assets(sample_plan, output_dir=str(tmp_path))

    # Verify results
    assert len(assets) == 3 # A, B, C
    assert assets['A'] == os.path.join(str(tmp_path), "keyframe_A.png")
    assert assets['B'] == os.path.join(str(tmp_path), "keyframe_B.png")
    assert assets['C'] == os.path.join(str(tmp_path), "keyframe_C.png")

    # Verify calls
    assert mock_client.models.generate_content.call_count == 3

    # Verify files created
    assert os.path.exists(os.path.join(str(tmp_path), "keyframe_A.png"))
    assert os.path.exists(os.path.join(str(tmp_path), "keyframe_B.png"))
    assert os.path.exists(os.path.join(str(tmp_path), "keyframe_C.png"))
