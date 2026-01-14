import os
from typing import List
from datetime import datetime
import openpyxl
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font, Alignment, PatternFill
from PIL import Image as PILImage
from pathlib import Path

from ..core.report_models import ReportRow
from ..utils.logger import setup_logger

logger = setup_logger()

class ReportService:
    """
    Generates visual Excel reports for batch video generation.
    Follows SRP by handling only Excel generation logic.
    """

    def __init__(self):
        self.thumbnail_height = 100  # pixels
        self.thumbnail_width = 100   # pixels
        self.column_width = 15       # approx characters (1 unit ~ 7px)

    def generate_report(self, rows: List[ReportRow], output_path: str) -> str:
        """
        Generates an Excel report from a list of ReportRows.

        Args:
            rows: List of data objects to report on.
            output_path: Path where the Excel file should be saved.

        Returns:
            The absolute path to the generated Excel file.
        """
        logger.info(f"Generating report with {len(rows)} rows to {output_path}")

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Generation Report"

        # Define Headers
        headers = [
            "Title", "Description", "Scenes", "Tags", "Generated At",
            "Output Path", "Recommended Option", "Thumbnails"
        ]

        # Write Headers with Style
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")

        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # Set Column Widths
        ws.column_dimensions['A'].width = 30  # Title
        ws.column_dimensions['B'].width = 50  # Description
        ws.column_dimensions['C'].width = 10  # Scenes
        ws.column_dimensions['D'].width = 20  # Tags
        ws.column_dimensions['E'].width = 20  # Generated At
        ws.column_dimensions['F'].width = 40  # Output Path
        ws.column_dimensions['G'].width = 15  # Recommended Option
        ws.column_dimensions['H'].width = 50  # Thumbnails area (will expand if needed)

        # Write Data
        for row_idx, data in enumerate(rows, 2):
            ws.cell(row=row_idx, column=1, value=data.title).alignment = Alignment(wrap_text=True, vertical="top")
            ws.cell(row=row_idx, column=2, value=data.description).alignment = Alignment(wrap_text=True, vertical="top")
            ws.cell(row=row_idx, column=3, value=data.scene_count).alignment = Alignment(horizontal="center", vertical="top")
            ws.cell(row=row_idx, column=4, value=", ".join(data.tags)).alignment = Alignment(wrap_text=True, vertical="top")
            ws.cell(row=row_idx, column=5, value=data.generated_at.strftime("%Y-%m-%d %H:%M")).alignment = Alignment(horizontal="center", vertical="top")
            ws.cell(row=row_idx, column=6, value=data.output_dir).alignment = Alignment(wrap_text=True, vertical="top")

            rec_opt = f"Option {data.recommended_metadata_option}" if data.recommended_metadata_option else "N/A"
            ws.cell(row=row_idx, column=7, value=rec_opt).alignment = Alignment(horizontal="center", vertical="top")

            # Handle Thumbnails
            current_col = 8
            if data.thumbnail_paths:
                # Adjust row height to fit image
                ws.row_dimensions[row_idx].height = 80 # approx points (1 pt = 1/72 inch)

                for img_path in data.thumbnail_paths:
                    if not img_path or not os.path.exists(img_path):
                        continue

                    try:
                        # Resize image for thumbnail using Pillow
                        pil_img = PILImage.open(img_path)
                        pil_img.thumbnail((self.thumbnail_width, self.thumbnail_height))

                        # Add to Excel
                        img = ExcelImage(pil_img)
                        # Position nicely in the cell (anchor is top-left)
                        # OpenPyXL doesn't support easy centering of images in cells, so we anchor to top-left

                        # We need to anchor it to the correct cell.
                        # Since we might have multiple images, we can expand to subsequent columns
                        # or put them all in one wide column?
                        # Let's use subsequent columns for multiple thumbnails.

                        cell_loc = ws.cell(row=row_idx, column=current_col)
                        img.anchor = cell_loc.coordinate
                        ws.add_image(img)

                        current_col += 1
                    except Exception as e:
                        logger.error(f"Failed to process thumbnail {img_path}: {e}")
                        ws.cell(row=row_idx, column=current_col, value="[Image Error]")
                        current_col += 1

        # Save
        try:
            wb.save(output_path)
            logger.info(f"Report saved successfully to {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            raise
