import sys
import os
from unittest.mock import MagicMock
import pytest
from google.genai import types

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_genai_client():
    mock_client = MagicMock()
    # Mock the generate_content return value
    mock_response = MagicMock()

    # Create a real Pydantic Part object to avoid validation errors
    # Note: inline_data must be populated correctly
    mock_part = types.Part(
        inline_data=types.Blob(
            data=b"fake_image_data",
            mime_type="image/png"
        )
    )

    # Set the parts on the mocked response
    mock_response.parts = [mock_part]
    mock_client.models.generate_content.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_plan():
    from core.models import VideoPlan, Scene

    scene1 = Scene(
        scene_number=1,
        action_description="Action 1",
        audio_prompt="Audio 1",
        start_pose_description="Pose 1 Start",
        end_pose_description="Pose 1 End"
    )
    scene2 = Scene(
        scene_number=2,
        action_description="Action 2",
        audio_prompt="Audio 2",
        start_pose_description="Pose 2 Start",
        end_pose_description="Pose 2 End"
    )

    return VideoPlan(
        title="Test Plan",
        description="Test Description",
        backend_tags=["tag1"],
        character_leader_desc="Leader",
        character_follower_desc="Follower",
        setting_desc="Setting",
        scenes=[scene1, scene2]
    )
