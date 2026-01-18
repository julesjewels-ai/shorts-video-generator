from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel

class StreamChunkType(str, Enum):
    TEXT = "text"
    THOUGHT = "thought"
    PLAN = "plan"
    ERROR = "error"

class StreamChunk(BaseModel):
    type: StreamChunkType
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
