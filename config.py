import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the package directory
_package_dir = Path(__file__).parent
load_dotenv(_package_dir / ".env")

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_VERSION = "v1beta"  # Required for response_mime_type, systemInstruction, thinkingConfig
    MODEL_NAME_TEXT = "gemini-3-pro-preview" # gemini-3-pro-preview gemini-2.5-flash
    MODEL_NAME_IMAGE = "gemini-3-pro-image-preview" # gemini-2.5-flash-image gemini-3-pro-image-preview

    # Paths
    OUTPUT_DIR = "Output"
    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
    
    # CSV Batch Processing
    CSV_INPUT_PATH = os.getenv("CSV_INPUT_PATH", None)
    CSV_AUTO_UPDATE = os.getenv("CSV_AUTO_UPDATE", "true").lower() == "true"
    CSV_CREATE_BACKUP = os.getenv("CSV_CREATE_BACKUP", "true").lower() == "true"
    
    # Scene Variety Control (0-10 scale)
    SCENE_VARIETY = int(os.getenv("SCENE_VARIETY", "5"))
    
    @classmethod
    def validate(cls):
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")


