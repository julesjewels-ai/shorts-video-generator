"""Pydantic models for web API requests and responses."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class GenerationMode(str, Enum):
    """Generation mode enum."""
    SINGLE = "single"
    BATCH = "batch"


class GenerationStatus(str, Enum):
    """Generation status enum."""
    IDLE = "idle"
    PLANNING = "planning"
    GENERATING_ASSETS = "generating_assets"
    CREATING_VEO = "creating_veo"
    GENERATING_SEO = "generating_seo"
    COMPLETE = "complete"
    ERROR = "error"


class ConfigRequest(BaseModel):
    """Request to update configuration."""
    leader_outfit: Optional[str] = None
    follower_outfit: Optional[str] = None
    setting: Optional[str] = None
    metadata_language: Optional[str] = None
    target_keywords: Optional[List[str]] = None
    scene_variety: Optional[int] = Field(None, ge=0, le=10)


class ConfigResponse(BaseModel):
    """Current configuration response."""
    leader_outfit: str
    follower_outfit: str
    setting: str
    metadata_language: str
    target_keywords: List[str]
    scene_variety: int
    reference_poses: List[str]  # List of available reference pose filenames


class GenerateSingleRequest(BaseModel):
    """Request to generate a single video."""
    user_request: Optional[str] = None
    scene_variety: Optional[int] = Field(None, ge=0, le=10)
    reference_pose_index: Optional[int] = Field(0, ge=0)


class GenerateBatchRequest(BaseModel):
    """Request to generate videos from CSV."""
    csv_content: str  # Raw CSV content


class KeyframeAsset(BaseModel):
    """A single keyframe asset."""
    scene: str  # e.g., "A", "B", "C", "D"
    filename: str
    url: str  # Relative URL to serve the image


class SceneInfo(BaseModel):
    """Information about a single scene."""
    scene_number: int
    action_description: str
    audio_prompt: str
    start_pose: str
    end_pose: str


class GenerationProgress(BaseModel):
    """Real-time generation progress update."""
    status: GenerationStatus
    message: str
    progress_percent: int = Field(ge=0, le=100)
    current_stage: str
    keyframes: List[KeyframeAsset] = []
    plan_title: Optional[str] = None
    scenes: List[SceneInfo] = []


class GenerationResult(BaseModel):
    """Complete generation result."""
    success: bool
    output_dir: str
    title: str
    keyframes: List[KeyframeAsset]
    scenes: List[SceneInfo]
    metadata: Optional[Dict[str, Any]] = None
    veo_instructions_url: Optional[str] = None
    error: Optional[str] = None


class OutputRun(BaseModel):
    """Summary of a completed generation run."""
    run_id: str
    title: str
    timestamp: str
    output_dir: str
    thumbnail_url: Optional[str] = None


class OutputRunDetail(BaseModel):
    """Detailed view of a completed generation run."""
    run_id: str
    title: str
    timestamp: str
    output_dir: str
    keyframes: List[KeyframeAsset]
    scenes: List[SceneInfo]
    metadata: Optional[Dict[str, Any]] = None
    veo_instructions: Optional[Dict[str, Any]] = None

class PlanRequest(BaseModel):
    user_prompt: str
