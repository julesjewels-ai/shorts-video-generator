from abc import ABC, abstractmethod
from typing import Dict, Any, Generator
from .models import VideoPlan
from .stream_models import StreamChunk

class IDirector(ABC):
    @abstractmethod
    def generate_plan(self, user_input: str) -> VideoPlan:
        pass

    @abstractmethod
    def generate_plan_stream(self, user_input: str) -> Generator[StreamChunk, None, None]:
        pass

class ICinematographer(ABC):
    @abstractmethod
    def generate_assets(self, plan: VideoPlan, output_dir: str = None) -> Dict[str, str]:
        pass

class IVeoInstruction(ABC):
    @abstractmethod
    def generate_instructions(self, plan: VideoPlan, asset_map: Dict[str, str], output_dir: str = None) -> None:
        pass
