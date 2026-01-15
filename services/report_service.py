import os
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from dance_loop_gen.core.report_models import ReportData
from dance_loop_gen.utils.logger import setup_logger

logger = setup_logger()

class ReportService:
    """Service for generating Excel reports with embedded visuals."""

    def generate_report(self, data: ReportData, output_path: str) -> str:
        """
        Generates an Excel report from ReportData.

        Args:
            data: The populated ReportData object.
            output_path: The file path where the Excel file should be saved.

        Returns:
            The output_path.
        """
        logger.info(f"Generating Excel report for: {data.title}")
        wb = Workbook()
        ws = wb.active
        ws.title = "Production Schedule"

        # Metadata Header
        ws.merge_cells('A1:G1')
        title_cell = ws['A1']
        title_cell.value = f"VIDEO PLAN: {data.title.upper()}"
        title_cell.font = Font(size=14, bold=True, color="FFFFFF")
        title_cell.fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        title_cell.alignment = Alignment(horizontal="center", vertical="center")

        ws.merge_cells('A2:G2')
        meta_cell = ws['A2']
        meta_cell.value = f"Run ID: {data.run_id} | Generated: {data.generated_at}"
        meta_cell.font = Font(italic=True, color="555555")
        meta_cell.alignment = Alignment(horizontal="center", vertical="center")

        # Table Headers
        headers = ["Scene", "Keyframe", "Action", "Audio", "Start Pose", "End Pose", "Notes"]
        header_row = 4

        # Style headers
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="36454F", end_color="36454F", fill_type="solid")
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                             top=Side(style='thin'), bottom=Side(style='thin'))

        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col_num, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = thin_border

        # Set column widths
        ws.column_dimensions['A'].width = 8   # Scene
        ws.column_dimensions['B'].width = 25  # Keyframe
        ws.column_dimensions['C'].width = 40  # Action
        ws.column_dimensions['D'].width = 25  # Audio
        ws.column_dimensions['E'].width = 25  # Start
        ws.column_dimensions['F'].width = 25  # End
        ws.column_dimensions['G'].width = 20  # Notes

        row_height = 130 # Height for image rows

        for i, row_data in enumerate(data.rows, start=header_row + 1):
            ws.row_dimensions[i].height = row_height

            # Scene Number
            c1 = ws.cell(row=i, column=1, value=row_data.scene_number)
            c1.alignment = Alignment(horizontal="center", vertical="center")
            c1.font = Font(bold=True, size=12)
            c1.border = thin_border

            # Keyframe Image
            c2 = ws.cell(row=i, column=2)
            c2.border = thin_border
            if row_data.keyframe_path and os.path.exists(row_data.keyframe_path):
                try:
                    img = XLImage(row_data.keyframe_path)

                    # Target height in pixels (approx)
                    target_height = 160

                    # Calculate scaling to fit
                    scale_h = target_height / img.height

                    new_height = target_height
                    new_width = int(img.width * scale_h)

                    img.height = new_height
                    img.width = new_width

                    # Center in cell B (approximate by adding margin)
                    # OpenPyXL places top-left.

                    cell_addr = f"B{i}"
                    ws.add_image(img, cell_addr)
                except Exception as e:
                    logger.error(f"Failed to add image {row_data.keyframe_path}: {e}")
                    c2.value = "[Image Error]"
                    c2.alignment = Alignment(horizontal="center", vertical="center")
            else:
                c2.value = "[No Image]"
                c2.alignment = Alignment(horizontal="center", vertical="center")

            # Text Columns
            c3 = ws.cell(row=i, column=3, value=row_data.action_description)
            c3.alignment = Alignment(wrap_text=True, vertical="center")
            c3.border = thin_border

            c4 = ws.cell(row=i, column=4, value=row_data.audio_prompt)
            c4.alignment = Alignment(wrap_text=True, vertical="center")
            c4.border = thin_border

            c5 = ws.cell(row=i, column=5, value=row_data.start_pose)
            c5.alignment = Alignment(wrap_text=True, vertical="center")
            c5.border = thin_border

            c6 = ws.cell(row=i, column=6, value=row_data.end_pose)
            c6.alignment = Alignment(wrap_text=True, vertical="center")
            c6.border = thin_border

            c7 = ws.cell(row=i, column=7, value=row_data.notes)
            c7.alignment = Alignment(wrap_text=True, vertical="center")
            c7.border = thin_border

        # Save
        wb.save(output_path)
        logger.info(f"Report saved to: {output_path}")
        return output_path
