import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from openpyxl import load_workbook
from dance_loop_gen.core.report_models import ReportRow
from dance_loop_gen.services.report_service import ReportService

class TestReportService(unittest.TestCase):
    def setUp(self):
        self.report_service = ReportService()
        self.output_path = "test_report.xlsx"

    def tearDown(self):
        if os.path.exists(self.output_path):
            os.remove(self.output_path)

    @patch("dance_loop_gen.services.report_service.PILImage")
    def test_generate_report(self, mock_pil):
        # Setup mock image
        mock_img = MagicMock()
        mock_pil.open.return_value = mock_img

        # Create dummy data
        row1 = ReportRow(
            title="Video 1",
            description="Description 1",
            output_dir="/tmp/video1",
            scene_count=3,
            tags=["tag1", "tag2"],
            recommended_metadata_option=1,
            thumbnail_paths=["/tmp/img1.png"]
        )
        row2 = ReportRow(
            title="Video 2",
            description="Description 2",
            output_dir="/tmp/video2",
            scene_count=5,
            tags=["tag3"],
            recommended_metadata_option=2,
            thumbnail_paths=[]
        )

        # Mock file existence for image path
        with patch("os.path.exists", return_value=True):
             self.report_service.generate_report([row1, row2], self.output_path)

        # Verify file creation
        self.assertTrue(os.path.exists(self.output_path))

        # Verify content
        wb = load_workbook(self.output_path)
        ws = wb.active

        self.assertEqual(ws.title, "Generation Report")

        # Check headers
        self.assertEqual(ws["A1"].value, "Title")
        self.assertEqual(ws["H1"].value, "Thumbnails")

        # Check Row 1
        self.assertEqual(ws["A2"].value, "Video 1")
        self.assertEqual(ws["C2"].value, 3)
        self.assertEqual(ws["G2"].value, "Option 1")

        # Check Row 2
        self.assertEqual(ws["A3"].value, "Video 2")
        self.assertEqual(ws["C3"].value, 5)
        self.assertEqual(ws["G3"].value, "Option 2")

        wb.close()

if __name__ == '__main__':
    unittest.main()
