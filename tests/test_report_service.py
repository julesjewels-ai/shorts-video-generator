"""Tests for ReportService."""

import os
import shutil
import tempfile
import pytest
from PIL import Image
from openpyxl import load_workbook
from dance_loop_gen.core.models import ProcessingResult
from dance_loop_gen.services.report_service import ReportService

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_image(temp_dir):
    """Create a sample image for testing."""
    img_path = os.path.join(temp_dir, "test_image.png")
    img = Image.new('RGB', (100, 100), color='red')
    img.save(img_path)
    return img_path

def test_generate_excel_report(temp_dir, sample_image):
    """Test generating an Excel report."""
    service = ReportService()

    # Create sample results
    results = [
        ProcessingResult(
            title="Test Video 1",
            output_dir="/tmp/output/test1",
            status="success",
            timestamp="2023-10-27 10:00:00",
            keyframe_paths=[sample_image],
            csv_row_index=1
        ),
        ProcessingResult(
            title="Test Video 2",
            output_dir="/tmp/output/test2",
            status="failed",
            timestamp="2023-10-27 10:05:00",
            keyframe_paths=[],
            csv_row_index=2
        )
    ]

    report_path = os.path.join(temp_dir, "report.xlsx")
    generated_path = service.generate_excel_report(results, report_path)

    # Verify file exists
    assert os.path.exists(generated_path)

    # Verify content
    wb = load_workbook(generated_path)
    ws = wb.active

    # Check headers
    assert ws['A1'].value == "ID"
    assert ws['B1'].value == "Title"
    assert ws['G1'].value == "Keyframe Preview"

    # Check data row 1
    assert ws['A2'].value == 1
    assert ws['B2'].value == "Test Video 1"
    assert ws['C2'].value == "success"
    # Check if image was added (images are stored in _images list)
    assert len(ws._images) == 1

    # Check data row 2
    assert ws['A3'].value == 2
    assert ws['B3'].value == "Test Video 2"
    assert ws['C3'].value == "failed"
    assert ws['G3'].value == "[No Keyframes]"
