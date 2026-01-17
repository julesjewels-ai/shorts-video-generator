import unittest
from unittest.mock import MagicMock, patch, ANY
import os
from datetime import datetime
from dance_loop_gen.services.video_processor import VideoProcessor
from dance_loop_gen.core.report_models import ReportRow, ReportData

class TestVideoProcessor(unittest.TestCase):

    def setUp(self):
        self.mock_director = MagicMock()
        self.mock_cinematographer = MagicMock()
        self.mock_veo = MagicMock()
        self.mock_seo = MagicMock()
        self.mock_report_service = MagicMock()

        # Mock Plan
        self.mock_plan = MagicMock()
        self.mock_plan.title = "Test Video"
        self.mock_plan.scenes = []
        for i in range(2):
            scene = MagicMock()
            scene.scene_number = i + 1
            scene.action_description = f"Action {i}"
            scene.audio_prompt = f"Audio {i}"
            scene.start_pose_description = f"Start {i}"
            scene.end_pose_description = f"End {i}"
            self.mock_plan.scenes.append(scene)

        self.mock_director.generate_plan.return_value = self.mock_plan

        # Mock Assets
        self.mock_assets = {
            'A': '/path/to/keyframe_a.png',
            'B': '/path/to/keyframe_b.png'
        }
        self.mock_cinematographer.generate_assets.return_value = self.mock_assets

    @patch('dance_loop_gen.services.video_processor.VideoProcessor._create_output_directory')
    @patch('dance_loop_gen.services.video_processor.save_state')
    @patch('dance_loop_gen.services.video_processor.logger')
    def test_process_flow(self, mock_logger, mock_save_state, mock_create_dir):
        mock_create_dir.return_value = "/tmp/output_dir"

        output_dir = VideoProcessor.process(
            user_request="make a dance video",
            director=self.mock_director,
            cinematographer=self.mock_cinematographer,
            veo=self.mock_veo,
            seo_specialist=self.mock_seo,
            report_service=self.mock_report_service
        )

        # Verify orchestrations
        self.mock_director.generate_plan.assert_called_once()
        self.mock_cinematographer.generate_assets.assert_called_once()
        self.mock_veo.generate_instructions.assert_called_once()
        self.mock_seo.generate_alternatives.assert_called_once()

        # Verify Report Generation
        self.mock_report_service.generate_report.assert_called_once()
        call_args = self.mock_report_service.generate_report.call_args
        report_data = call_args[0][0]
        report_path = call_args[0][1]

        self.assertIsInstance(report_data, ReportData)
        self.assertEqual(report_data.title, "Test Video")
        self.assertEqual(len(report_data.rows), 2)
        self.assertEqual(report_data.rows[0].keyframe_path, '/path/to/keyframe_a.png')
        self.assertTrue(report_path.endswith("production_report.xlsx"))

        self.assertEqual(output_dir, "/tmp/output_dir")

    @patch('dance_loop_gen.services.video_processor.VideoProcessor._create_output_directory')
    @patch('dance_loop_gen.services.video_processor.save_state')
    @patch('dance_loop_gen.services.video_processor.logger')
    def test_process_without_report_service(self, mock_logger, mock_save_state, mock_create_dir):
        mock_create_dir.return_value = "/tmp/output_dir"

        output_dir = VideoProcessor.process(
            user_request="make a dance video",
            director=self.mock_director,
            cinematographer=self.mock_cinematographer,
            veo=self.mock_veo,
            seo_specialist=self.mock_seo,
            report_service=None
        )

        self.mock_report_service.generate_report.assert_not_called()
        self.assertEqual(output_dir, "/tmp/output_dir")

if __name__ == '__main__':
    unittest.main()
