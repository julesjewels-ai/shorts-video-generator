"""Service for generating consolidated Excel reports with visual data.

This service follows the Single Responsibility Principle by encapsulating
all reporting logic, separating it from the batch orchestration.
"""

import os
from datetime import datetime
from typing import List
from openpyxl import Workbook
from openpyxl.drawing.image import Image
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

from dance_loop_gen.core.models import ProcessingResult
from dance_loop_gen.utils.logger import setup_logger, console

logger = setup_logger()


class ReportService:
    """Generates Excel reports from processing results."""

    def __init__(self):
        """Initialize the report service."""
        pass

    def generate_excel_report(self, results: List[ProcessingResult], output_path: str) -> str:
        """Generate an Excel report with thumbnails for the processed videos.

        Args:
            results: List of processing results
            output_path: Path where the Excel file should be saved

        Returns:
            Path to the generated Excel file
        """
        logger.info(f"Generating Excel report for {len(results)} items...")
        console.print(f"[bold blue]📊 Generating Excel Report...[/bold blue]")

        wb = Workbook()
        ws = wb.active
        ws.title = "Processing Report"

        # Define headers
        headers = [
            "ID", "Title", "Status", "Timestamp", "Output Directory",
            "Metadata JSON", "Keyframe Preview"
        ]

        # Style headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")

        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Set column widths
        ws.column_dimensions['A'].width = 10  # ID
        ws.column_dimensions['B'].width = 30  # Title
        ws.column_dimensions['C'].width = 15  # Status
        ws.column_dimensions['D'].width = 20  # Timestamp
        ws.column_dimensions['E'].width = 40  # Output Dir
        ws.column_dimensions['F'].width = 30  # Metadata
        ws.column_dimensions['G'].width = 40  # Keyframe (will hold image)

        # Add data rows
        for row_idx, result in enumerate(results, 2):
            # Row height needs to be tall enough for the image
            ws.row_dimensions[row_idx].height = 100

            # Text data
            ws.cell(row=row_idx, column=1, value=result.csv_row_index if result.csv_row_index else row_idx-1)
            ws.cell(row=row_idx, column=2, value=result.title).alignment = Alignment(wrap_text=True, vertical="center")

            status_cell = ws.cell(row=row_idx, column=3, value=result.status)
            status_cell.alignment = Alignment(horizontal="center", vertical="center")
            if result.status == "success":
                status_cell.font = Font(color="008000", bold=True)
            else:
                status_cell.font = Font(color="FF0000", bold=True)

            ws.cell(row=row_idx, column=4, value=result.timestamp).alignment = Alignment(horizontal="center", vertical="center")

            # Link to output directory
            dir_cell = ws.cell(row=row_idx, column=5, value=os.path.basename(result.output_dir))
            dir_cell.hyperlink = result.output_dir
            dir_cell.font = Font(color="0563C1", underline="single")
            dir_cell.alignment = Alignment(vertical="center")

            # Metadata path
            if result.metadata_path:
                meta_cell = ws.cell(row=row_idx, column=6, value=os.path.basename(result.metadata_path))
                meta_cell.alignment = Alignment(vertical="center")

            # Add Image (Thumbnail)
            if result.keyframe_paths:
                # Use the first keyframe (usually 'A')
                img_path = result.keyframe_paths[0]
                if os.path.exists(img_path):
                    try:
                        img = Image(img_path)
                        # Resize for thumbnail
                        img.height = 120
                        img.width = 120 * (img.width / img.height)

                        # Add to cell (G column)
                        cell_addr = f"G{row_idx}"
                        ws.add_image(img, cell_addr)
                    except Exception as e:
                        logger.warning(f"Failed to add image to report for {result.title}: {e}")
                        ws.cell(row=row_idx, column=7, value="[Image Error]")
                else:
                    ws.cell(row=row_idx, column=7, value="[Image Missing]")
            else:
                ws.cell(row=row_idx, column=7, value="[No Keyframes]")

        # Save workbook
        try:
            wb.save(output_path)
            logger.info(f"Report saved to {output_path}")
            console.print(f"[bold green]✔ Report saved:[/bold green] {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save Excel report: {e}")
            raise
