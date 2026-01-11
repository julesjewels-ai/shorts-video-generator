from dance_loop_gen.core.models import CSVRow
from dance_loop_gen.utils.prompt_loader import PromptLoader


def build_request_from_csv(csv_row: CSVRow, base_request: str = "") -> str:
    """Build an enriched user request from a CSV row and optional base template.
    
    Args:
        csv_row: The CSV row data
        base_request: Optional base user request template
        
    Returns:
        Enriched user request string with CSV data
    """
    
    # Build the enriched context
    parts = []
    
    # Creative Direction Section
    parts.append("=" * 60)
    parts.append("CREATIVE DIRECTION FROM CSV")
    parts.append("=" * 60)
    parts.append(f"Style: {csv_row.style}")
    parts.append(f"Music Type: {csv_row.music}")
    parts.append(f"Duration: {csv_row.duration}")
    parts.append("")
    
    # Concept Description
    parts.append("CONCEPT DESCRIPTION")
    parts.append("-" * 60)
    parts.append(csv_row.description)
    parts.append("")
    
    # Target Metadata
    parts.append("TARGET METADATA")
    parts.append("-" * 60)
    if csv_row.improved_title:
        parts.append(f"Suggested Title (Spanish): {csv_row.improved_title}")
    if csv_row.improved_title_english:
        parts.append(f"Suggested Title (English): {csv_row.improved_title_english}")
    parts.append(f"Keywords: {csv_row.keywords_tags}")
    parts.append("")
    
    # Additional Base Context (if provided)
    if base_request and base_request.strip():
        parts.append("ADDITIONAL CONTEXT")
        parts.append("-" * 60)
        parts.append(base_request.strip())
        parts.append("")
    
    parts.append("=" * 60)
    
    return "\n".join(parts)


def get_default_setting_description() -> str:
    """Return a default setting description that is subtle and dancer-focused.
    
    This is used when no setting.txt is provided and no specific setting 
    is defined in the CSV data.
    
    Returns:
        A clean, subtle setting description
    """
    return (
        "A clean, subtle background with soft natural lighting. "
        "The setting should add to the mood without being distracting. "
        "Keep the focus entirely on the dancers and their movement. "
        "Use minimal, elegant environmental details."
    )
