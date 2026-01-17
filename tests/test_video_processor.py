import unittest
from unittest.mock import MagicMock, patch
from dance_loop_gen.services.video_processor import VideoProcessor
from dance_loop_gen.core.models import VideoPlan, Scene, CSVRow
from dance_loop_gen.core.report_models import ReportData

class TestVideoProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_director = MagicMock()
        self.mock_cinematographer = MagicMock()
        self.mock_veo = MagicMock()
        self.mock_seo = MagicMock()
        self.mock_report_service = MagicMock()

        # Setup mock plan
        self.mock_plan = VideoPlan(
            title="Test Video",
            description="Test description",
            backend_tags=["dance"],
            character_leader_desc="Leader",
            character_follower_desc="Follower",
            setting_desc="Setting",
            scenes=[
                Scene(
                    scene_number=1,
                    action_description="Action",
                    audio_prompt="Audio",
                    start_pose_description="Start",
                    end_pose_description="End"
                )
            ]
        )
        self.mock_director.generate_plan.return_value = self.mock_plan

        # Setup mock assets
        self.mock_assets = {"A": "/path/to/keyframe_A.png"}
        self.mock_cinematographer.generate_assets.return_value = self.mock_assets

        # Setup mock SEO
        mock_metadata_alternatives = MagicMock()
        mock_metadata_alternatives.recommended = 1
        mock_metadata_alternatives.reasoning = "Test reasoning"
        self.mock_seo.load_config.return_value = MagicMock()
        self.mock_seo.generate_alternatives.return_value = mock_metadata_alternatives
        self.mock_seo.save_metadata.return_value = ("json_path", "csv_path")

    @patch('dance_loop_gen.services.video_processor.save_state')
    @patch('dance_loop_gen.services.video_processor.VideoProcessor._create_output_directory')
    def test_process_flow(self, mock_create_dir, mock_save_state):
        mock_create_dir.return_value = "/tmp/test_output"

        VideoProcessor.process(
            user_request="Test request",
            director=self.mock_director,
            cinematographer=self.mock_cinematographer,
            veo=self.mock_veo,
            seo_specialist=self.mock_seo,
            report_service=self.mock_report_service
        )

        # Verify calls
        self.mock_director.generate_plan.assert_called_once()
        self.mock_cinematographer.generate_assets.assert_called_once()
        self.mock_veo.generate_instructions.assert_called_once()
        self.mock_seo.generate_alternatives.assert_called_once()

        # Verify Report Service called
        self.mock_report_service.generate_report.assert_called_once()
        args, _ = self.mock_report_service.generate_report.call_args
        report_data = args[0]
        self.assertIsInstance(report_data, ReportData)
        self.assertEqual(report_data.title, "Test Video")
        self.assertEqual(len(report_data.rows), 1)
