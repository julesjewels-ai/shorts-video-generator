from typing import Any, Optional, Union
from pydantic import BaseModel, Field

class StreamChunkType(str):
    THOUGHT = "thought"
    TEXT = "text"
    JSON_PARTIAL = "json_partial"
    RESULT = "result"
    ERROR = "error"

class StreamChunk(BaseModel):
    """Represents a chunk of data streaming from the AI."""
    type: str = Field(description="The type of the chunk (thought, text, result, etc.)")
    content: Optional[str] = Field(None, description="The text content of the chunk")
    data: Optional[Any] = Field(None, description="Structured data (e.g. the final plan)")
