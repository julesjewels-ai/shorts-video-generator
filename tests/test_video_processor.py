import unittest
from unittest.mock import MagicMock, patch
import os

from dance_loop_gen.services.video_processor import VideoProcessor
from dance_loop_gen.core.models import VideoPlan, Scene, MetadataAlternatives, MetadataOption
from dance_loop_gen.core.report_models import ReportData

class TestVideoProcessor(unittest.TestCase):
    def setUp(self):
        self.mock_director = MagicMock()
        self.mock_cinematographer = MagicMock()
        self.mock_veo = MagicMock()
        self.mock_seo = MagicMock()
        self.mock_report_service = MagicMock()

        # Setup mock return values
        self.mock_plan = VideoPlan(
            title="Test Video",
            description="Test Description",
            backend_tags=["tag1"],
            character_leader_desc="Leader",
            character_follower_desc="Follower",
            setting_desc="Setting",
            scenes=[
                Scene(
                    scene_number=1,
                    action_description="Action 1",
                    audio_prompt="Audio 1",
                    start_pose_description="Start 1",
                    end_pose_description="End 1"
                ),
                Scene(
                    scene_number=2,
                    action_description="Action 2",
                    audio_prompt="Audio 2",
                    start_pose_description="Start 2",
                    end_pose_description="End 2"
                )
            ]
        )
        self.mock_director.generate_plan.return_value = self.mock_plan

        self.mock_assets = {
            "A": "/path/to/A.png",
            "B": "/path/to/B.png"
        }
        self.mock_cinematographer.generate_assets.return_value = self.mock_assets

        self.mock_seo.load_config.return_value = MagicMock()
        self.mock_seo.generate_alternatives.return_value = MetadataAlternatives(
            option_1=MetadataOption(title="T1", description="D1", tags=["t1"], emotional_hook="H1", text_hook="TH1", text_overlay=["TO1"]),
            option_2=MetadataOption(title="T2", description="D2", tags=["t2"], emotional_hook="H2", text_hook="TH2", text_overlay=["TO2"]),
            option_3=MetadataOption(title="T3", description="D3", tags=["t3"], emotional_hook="H3", text_hook="TH3", text_overlay=["TO3"]),
            recommended=1,
            reasoning="Because"
        )
        self.mock_seo.save_metadata.return_value = ("json_path", "csv_path")

    @patch("dance_loop_gen.services.video_processor.VideoProcessor._create_output_directory")
    @patch("dance_loop_gen.services.video_processor.save_state")
    def test_process_generates_report(self, mock_save_state, mock_create_dir):
        # Arrange
        mock_create_dir.return_value = "/tmp/output_dir"

        # Act
        VideoProcessor.process(
            user_request="make a video",
            director=self.mock_director,
            cinematographer=self.mock_cinematographer,
            veo=self.mock_veo,
            seo_specialist=self.mock_seo,
            report_service=self.mock_report_service
        )

        # Assert
        self.mock_report_service.generate_report.assert_called_once()

        # Inspect arguments
        call_args = self.mock_report_service.generate_report.call_args
        report_data = call_args[0][0]
        output_path = call_args[0][1]

        self.assertIsInstance(report_data, ReportData)
        self.assertEqual(report_data.title, "Test Video")
        self.assertEqual(len(report_data.rows), 2)

        # Verify row content mapping
        row1 = report_data.rows[0]
        self.assertEqual(row1.scene_number, 1)
        self.assertEqual(row1.keyframe_path, "/path/to/A.png")
        self.assertEqual(row1.action_description, "Action 1")

        row2 = report_data.rows[1]
        self.assertEqual(row2.scene_number, 2)
        self.assertEqual(row2.keyframe_path, "/path/to/B.png")

        self.assertEqual(output_path, "/tmp/output_dir/production_report.xlsx")

if __name__ == "__main__":
    unittest.main()
