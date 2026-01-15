from typing import List, Optional
from pydantic import BaseModel, Field

class ReportRow(BaseModel):
    """Represents a single row in the production report (one scene)."""
    scene_number: int
    keyframe_path: Optional[str] = Field(description="Path to the generated keyframe image")
    action_description: str
    audio_prompt: str
    start_pose: str
    end_pose: str
    notes: Optional[str] = ""

class ReportData(BaseModel):
    """Container for the full report data."""
    title: str
    generated_at: str
    run_id: str
    rows: List[ReportRow]
