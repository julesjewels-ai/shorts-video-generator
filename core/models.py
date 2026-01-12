from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

class Scene(BaseModel):
    """Represents a single scene in the dance video."""
    scene_number: int
    action_description: str = Field(description="Description of movement for video generation (e.g., 'Leader spins follower')")
    audio_prompt: str = Field(description="Music/SFX prompt for Veo (e.g., 'Heels on wood, Spanish guitar, 120bpm')")
    start_pose_description: str = Field(description="Visual description of the starting pose")
    end_pose_description: str = Field(description="Visual description of the ending pose")

class VideoPlan(BaseModel):
    """Represents the complete plan for the dance video."""
    title: str
    description: str = Field(description="YouTube Short description with 5 hashtags and emojis")
    backend_tags: List[str]
    # The Director must define the Visual Style once for consistency
    character_leader_desc: str
    character_follower_desc: str
    setting_desc: str
    scenes: List[Scene]

class VeoTask(BaseModel):
    """Represents a single task for Veo video generation."""
    scene: int
    start_image: str
    end_image: str
    prompt: str
    audio: str


class MetadataOption(BaseModel):
    """A single metadata option with title, description, and tags."""
    title: str
    description: str = Field(description="YouTube Short description with hashtags and emojis")
    tags: List[str]
    emotional_hook: str = Field(description="The emotional response this option targets")
    text_hook: str = Field(description="Attention-grabbing text hook for the video overlay")
    text_overlay: List[str] = Field(description="Progressive text overlay snippets for the video")


class MetadataAlternatives(BaseModel):
    """Three alternative metadata options for the video."""
    option_1: MetadataOption
    option_2: MetadataOption
    option_3: MetadataOption
    recommended: int = Field(default=1, ge=1, le=3)
    reasoning: str = Field(description="Strategic explanation for the recommendation")


class MetadataConfig(BaseModel):
    """User configuration for metadata generation."""
    language: str = Field(default="English")
    target_keywords: Optional[List[str]] = Field(default=None)
    spreadsheet_content: Optional[str] = Field(default=None, description="Raw spreadsheet content sent to AI")


class CSVRow(BaseModel):
    """Represents a single row from the CSV input file."""
    created: bool = Field(description="Whether this video has been generated")
    style: str
    title_spanish: Optional[str] = Field(default=None)
    title_english: Optional[str] = Field(default=None)
    improved_title: Optional[str] = Field(default=None)
    improved_title_english: Optional[str] = Field(default=None)
    duration: str = Field(default="18s")
    music: str
    description: str
    keywords_tags: str
    scene_variety: Optional[int] = Field(default=None, ge=0, le=10, description="Scene variation level 0-10")
    
    # Store original row index for updating CSV
    row_index: int = Field(default=-1, exclude=True)
    
    class Config:
        populate_by_name = True

    @field_validator('style')
    @classmethod
    def style_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Style cannot be empty')
        return v.strip()

    @field_validator('duration')
    @classmethod
    def duration_must_be_valid(cls, v: str) -> str:
        if not v.endswith('s'):
            raise ValueError("Duration must end with 's' (e.g., '18s')")
        try:
            int(v[:-1])
        except ValueError:
            raise ValueError("Duration must be a number followed by 's'")
        return v



class CSVBatchConfig(BaseModel):
    """Configuration for CSV batch processing."""
    csv_path: str
    process_uncreated_only: bool = Field(default=True)
    update_created_flag: bool = Field(default=True)


class ProcessingResult(BaseModel):
    """Result of a single video generation task."""
    row_index: int
    style: str
    status: str = Field(description="Status of the generation: 'Success' or 'Failed'")
    output_dir: Optional[str] = Field(default=None, description="Path to the generated video directory")
    error_message: Optional[str] = Field(default=None, description="Error message if generation failed")
    duration_seconds: float = Field(description="Time taken to process in seconds")
