import csv
import os
from pathlib import Path
from typing import List, Dict, Any
from dance_loop_gen.core.models import CSVRow


class CSVHandler:
    """Handles reading and writing CSV batch files."""
    
    @staticmethod
    def _normalize_header(header: str) -> str:
        """Normalize CSV header names to match model field names."""
        # Remove spaces, convert to lowercase
        normalized = header.strip().lower().replace(" ", "_").replace("(", "_").replace(")", "")
        
        # Map specific headers to model field names
        field_mapping = {
            "title_spanish_": "title_spanish",
            "title_english_": "title_english",
            "improve_title_english": "improved_title_english",
            "keywords/tags": "keywords_tags",
        }
        
        return field_mapping.get(normalized, normalized)
    
    @staticmethod
    def read_csv(csv_path: str) -> List[CSVRow]:
        """Read CSV file and return list of CSVRow objects.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of CSVRow objects with row_index populated
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Normalize headers
            normalized_fieldnames = [CSVHandler._normalize_header(h) for h in reader.fieldnames]
            
            for idx, raw_row in enumerate(reader, start=2):  # start=2 because row 1 is header
                # Create normalized row dict
                normalized_row = {}
                for original_header, normalized_header in zip(reader.fieldnames, normalized_fieldnames):
                    value = raw_row[original_header]
                    normalized_row[normalized_header] = value
                
                # Convert 'created' to boolean
                created_value = normalized_row.get('created', 'FALSE').strip().upper()
                normalized_row['created'] = created_value in ['TRUE', '1', 'YES']
                
                try:
                    csv_row = CSVRow(**normalized_row)
                    csv_row.row_index = idx
                    rows.append(csv_row)
                except Exception as e:
                    print(f"Warning: Skipping row {idx} due to error: {e}")
                    continue
        
        return rows
    
    @staticmethod
    def get_pending_rows(csv_path: str) -> List[CSVRow]:
        """Return only rows where Created = FALSE.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            List of CSVRow objects where created=False
        """
        all_rows = CSVHandler.read_csv(csv_path)
        return [row for row in all_rows if not row.created]
    
    @staticmethod
    def mark_row_completed(csv_path: str, row_index: int):
        """Update the 'Created' column to TRUE for a specific row.
        
        Args:
            csv_path: Path to the CSV file
            row_index: The row index to update (1-indexed, including header)
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        # Read all rows using csv reader to handle quotes/commas correctly
        rows = []
        fieldnames = []
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            fieldnames = next(reader)
            rows = list(reader)
        
        # Update the specific row
        # row_index is 1-indexed (header is 1, so index - 2 is the row in list)
        list_index = row_index - 2
        
        if 0 <= list_index < len(rows):
            # Update first column (Created) - assuming it's always the first column
            rows[list_index][0] = 'TRUE'
            
            # Write back using csv writer
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(fieldnames)
                writer.writerows(rows)
        else:
            raise ValueError(f"Row index {row_index} out of range (file has {len(rows) + 1} lines)")
    
    @staticmethod
    def create_backup(csv_path: str) -> str:
        """Create a backup of the CSV file before processing.
        
        Args:
            csv_path: Path to the CSV file
            
        Returns:
            Path to the backup file
        """
        import shutil
        from datetime import datetime
        
        backup_path = csv_path.replace('.csv', f'_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        shutil.copy2(csv_path, backup_path)
        return backup_path
