import unittest
from unittest.mock import MagicMock, patch
from dance_loop_gen.services.director import DirectorService
from dance_loop_gen.core.stream_models import StreamChunk, StreamChunkType
from dance_loop_gen.core.models import VideoPlan

class TestDirectorStream(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock()
        self.director = DirectorService(self.mock_client)

    @patch('dance_loop_gen.utils.prompt_loader.PromptLoader.load')
    @patch('dance_loop_gen.utils.prompt_loader.PromptLoader.load_optional')
    def test_generate_plan_stream_success(self, mock_load_optional, mock_load):
        # Setup mocks for initialization
        mock_load.return_value = "System Instruction"
        mock_load_optional.return_value = None

        # Setup mock stream response
        chunk1 = MagicMock()
        chunk1.text = '{"title": "Test Video", "description": "Desc", "backend_tags": [], "character_leader_desc": "L", "character_follower_desc": "F", "setting_desc": "S", "scenes": []}'

        # Make the stream iterable
        self.mock_client.models.generate_content_stream.return_value = [chunk1]

        # Call method
        chunks = list(self.director.generate_plan_stream("test input"))

        # Verify calls
        self.mock_client.models.generate_content_stream.assert_called_once()

        # Verify output
        self.assertTrue(len(chunks) >= 2) # At least token + plan
        self.assertEqual(chunks[0].type, StreamChunkType.TOKEN)
        self.assertEqual(chunks[-1].type, StreamChunkType.PLAN)

        # Verify content
        plan_data = chunks[-1].content
        self.assertEqual(plan_data['title'], "Test Video")

    def test_generate_plan_stream_error(self):
        # Setup error
        self.mock_client.models.generate_content_stream.side_effect = Exception("API Error")

        # Call and expect error chunk before raise
        try:
            chunks = list(self.director.generate_plan_stream("test input"))
        except Exception as e:
            self.assertEqual(str(e), "API Error")

if __name__ == '__main__':
    unittest.main()
