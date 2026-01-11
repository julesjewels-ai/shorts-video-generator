from abc import ABC, abstractmethod
from typing import Dict, Any
from .models import VideoPlan

class IDirector(ABC):
    @abstractmethod
    def generate_plan(self, user_input: str) -> VideoPlan:
        pass

class ICinematographer(ABC):
    @abstractmethod
    def generate_assets(self, plan: VideoPlan, output_dir: str = None) -> Dict[str, str]:
        pass

class IVeoInstruction(ABC):
    @abstractmethod
    def generate_instructions(self, plan: VideoPlan, asset_map: Dict[str, str], output_dir: str = None) -> None:
        pass
