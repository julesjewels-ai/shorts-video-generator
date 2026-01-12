import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from dance_loop_gen.core.models import DirectorInput, VideoPlan, Scene
from dance_loop_gen.services.director import DirectorService

class TestDirectorSecurity:

    def test_director_input_valid(self):
        """Test that valid input is accepted."""
        valid_input = "Create a dance video with salsa style."
        model = DirectorInput(user_prompt=valid_input)
        assert model.user_prompt == valid_input

    def test_director_input_sanitization_whitespace(self):
        """Test that whitespace is stripped."""
        input_str = "   Trim me   "
        model = DirectorInput(user_prompt=input_str)
        assert model.user_prompt == "Trim me"

    def test_director_input_too_long(self):
        """Test that input longer than max length is rejected."""
        long_input = "a" * 2001
        with pytest.raises(ValidationError) as excinfo:
            DirectorInput(user_prompt=long_input)
        assert "String should have at most 2000 characters" in str(excinfo.value)

    def test_director_input_empty(self):
        """Test that empty input is rejected."""
        with pytest.raises(ValidationError) as excinfo:
            DirectorInput(user_prompt="")
        assert "String should have at least 1 character" in str(excinfo.value)

    def test_director_input_control_chars(self):
        """Test that input with control characters is rejected."""
        # \x00 is a null byte, definitely a control char
        bad_input = "Hello\x00World"
        with pytest.raises(ValidationError) as excinfo:
            DirectorInput(user_prompt=bad_input)
        assert "Input contains invalid control characters" in str(excinfo.value)

    def test_director_input_allowed_newlines(self):
        """Test that newlines are allowed."""
        good_input = "Line 1\nLine 2"
        model = DirectorInput(user_prompt=good_input)
        assert model.user_prompt == good_input

    def test_generate_plan_security_integration(self):
        """Test that DirectorService accepts DirectorInput and calls API safely."""
        # Mock Client
        mock_client = MagicMock()
        mock_response = MagicMock()

        # Create a valid minimal VideoPlan JSON response
        mock_plan_json = """
        {
            "title": "Test Video",
            "description": "A test video #dance",
            "backend_tags": ["test"],
            "character_leader_desc": "Leader",
            "character_follower_desc": "Follower",
            "setting_desc": "Studio",
            "scenes": [
                {
                    "scene_number": 1,
                    "action_description": "Spin",
                    "audio_prompt": "Music",
                    "start_pose_description": "Start",
                    "end_pose_description": "End"
                }
            ]
        }
        """
        mock_response.text = mock_plan_json
        mock_client.models.generate_content.return_value = mock_response

        service = DirectorService(client=mock_client)

        # Create secure input
        secure_input = DirectorInput(user_prompt="Make a salsa video")

        # Call generate_plan
        plan = service.generate_plan(secure_input)

        # Verify result
        assert isinstance(plan, VideoPlan)
        assert plan.title == "Test Video"

        # Verify API was called with the string content
        mock_client.models.generate_content.assert_called_once()
        call_args = mock_client.models.generate_content.call_args
        assert call_args.kwargs['contents'] == "Make a salsa video"

    def test_generate_plan_with_raw_string_conversion(self):
        """Test that DirectorService automatically converts raw string to DirectorInput."""
        # Mock Client
        mock_client = MagicMock()
        mock_response = MagicMock()

        # Create a valid minimal VideoPlan JSON response
        mock_plan_json = """
        {
            "title": "Test Video",
            "description": "A test video #dance",
            "backend_tags": ["test"],
            "character_leader_desc": "Leader",
            "character_follower_desc": "Follower",
            "setting_desc": "Studio",
            "scenes": [
                {
                    "scene_number": 1,
                    "action_description": "Spin",
                    "audio_prompt": "Music",
                    "start_pose_description": "Start",
                    "end_pose_description": "End"
                }
            ]
        }
        """
        mock_response.text = mock_plan_json
        mock_client.models.generate_content.return_value = mock_response

        service = DirectorService(client=mock_client)

        # Call generate_plan with RAW STRING
        plan = service.generate_plan("Make a salsa video")

        # Verify result
        assert isinstance(plan, VideoPlan)

        # Verify API was called
        mock_client.models.generate_content.assert_called_once()
