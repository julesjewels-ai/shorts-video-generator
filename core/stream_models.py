from enum import Enum
from typing import Optional, Any, Union
from pydantic import BaseModel

class StreamChunkType(str, Enum):
    TOKEN = "token"   # Partial text content
    PLAN = "plan"     # Final parsed VideoPlan object
    LOG = "log"       # Progress or status message
    ERROR = "error"   # Error message

class StreamChunk(BaseModel):
    """A standardized chunk of data for streaming responses."""
    type: StreamChunkType
    content: Union[str, dict, Any]

    class Config:
        use_enum_values = True
