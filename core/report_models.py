from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ReportRow(BaseModel):
    """Represents a single row in the generation report."""
    title: str
    description: str
    generated_at: datetime = Field(default_factory=datetime.now)
    output_dir: str
    scene_count: int
    tags: List[str]

    # Paths to key images for the report
    thumbnail_paths: List[str] = Field(default_factory=list, description="List of absolute paths to keyframe images to embed")

    # Metadata info
    recommended_metadata_option: Optional[int] = None

    class Config:
        arbitrary_types_allowed = True
