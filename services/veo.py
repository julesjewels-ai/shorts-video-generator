import json
import os
from typing import Dict
from ..core.interfaces import IVeoInstruction
from ..core.models import VideoPlan
from ..config import Config

class VeoService(IVeoInstruction):
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_instructions(self, plan: VideoPlan, asset_map: Dict[str, str], output_dir: str = None) -> None:
        print("📹 Generating Veo instructions...")
        
        target_dir = output_dir if output_dir else self.output_dir
        os.makedirs(target_dir, exist_ok=True) # Ensure directory exists
        
        veo_tasks = [
            {
                "scene": 1,
                "start_image": asset_map['A'],
                "end_image": asset_map['B'],
                "prompt": plan.scenes[0].action_description,
                "audio": plan.scenes[0].audio_prompt
            },
            {
                "scene": 2,
                "start_image": asset_map['B'],
                "end_image": asset_map['C'],
                "prompt": plan.scenes[1].action_description,
                "audio": plan.scenes[1].audio_prompt
            },
            {
                "scene": 3,
                "start_image": asset_map['C'],
                "end_image": asset_map['D'],
                "prompt": plan.scenes[2].action_description,
                "audio": plan.scenes[2].audio_prompt
            },
            {
                "scene": 4,
                "start_image": asset_map['D'],
                "end_image": asset_map['A'], # CLOSING THE LOOP
                "prompt": plan.scenes[3].action_description,
                "audio": plan.scenes[3].audio_prompt
            }
        ]
        
        output_path = os.path.join(target_dir, "veo_instructions.json")
        with open(output_path, "w") as f:
            json.dump(veo_tasks, f, indent=2)
            
        print(f"✅ Instructions saved to {output_path}")

