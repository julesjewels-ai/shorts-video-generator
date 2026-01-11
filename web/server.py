import os
import asyncio
import json
import logging
import zipfile
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from google import genai
from pydantic import BaseModel

from dance_loop_gen.config import Config
from dance_loop_gen.services.director import DirectorService
from dance_loop_gen.services.cinematographer import CinematographerService
from dance_loop_gen.services.veo import VeoService
from dance_loop_gen.services.seo_specialist import SEOSpecialistService
from dance_loop_gen.services.batch_orchestrator import BatchOrchestrator
from dance_loop_gen.services.video_processor import VideoProcessor
from dance_loop_gen.utils.prompt_loader import PromptLoader
from dance_loop_gen.utils.logger import setup_logger, get_run_dir
from dance_loop_gen.web.api_models import (
    ConfigRequest, ConfigResponse, GenerateSingleRequest, 
    GenerationStatus, GenerationProgress, GenerationResult,
    OutputRun, OutputRunDetail, KeyframeAsset, SceneInfo
)

# Initialize app
app = FastAPI(title="Dance Loop Generator")

# Build static paths
BASE_DIR = Path(__file__).parent.parent
STATIC_DIR = Path(__file__).parent / "static"
OUTPUT_DIR = Path(Config.OUTPUT_DIR)
PROMPTS_DIR = Path(Config.PROMPTS_DIR)

# Ensure static directory exists
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# State management for progress
class ProgressManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.current_progress: GenerationProgress = GenerationProgress(
            status=GenerationStatus.IDLE,
            message="Ready to generate",
            progress_percent=0,
            current_stage="Idle"
        )

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current state on connect
        await websocket.send_text(self.current_progress.model_dump_json())

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, progress: GenerationProgress):
        self.current_progress = progress
        message = progress.model_dump_json()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

progress_manager = ProgressManager()

# Service initialization helper
def get_services():
    client = genai.Client(http_options={'api_version': Config.GEMINI_VERSION})
    director = DirectorService(client)
    cinematographer = CinematographerService(client)
    veo = VeoService()
    seo_specialist = SEOSpecialistService(client)
    batch_orchestrator = BatchOrchestrator(director, cinematographer, veo, seo_specialist)
    return director, cinematographer, veo, seo_specialist, batch_orchestrator

# Custom Logger Interceptor for Web Progress
class WebLogHandler(logging.Handler):
    def __init__(self, loop, manager):
        super().__init__()
        self.loop = loop
        self.manager = manager

    def emit(self, record):
        msg = self.format(record)
        # We only want to broadcast significant messages to the UI
        # This is a bit simplistic; in a real app we'd map log levels/content to progress stages
        if self.manager.current_progress.status != GenerationStatus.IDLE:
            # Schedule the broadcast in the event loop
            asyncio.run_coroutine_threadsafe(
                self.update_ui(msg), self.loop
            )

    async def update_ui(self, message):
        prog = self.manager.current_progress
        prog.message = message
        
        # Simple stage mapping logic
        if "Director" in message:
            prog.status = GenerationStatus.PLANNING
            prog.current_stage = "Planning"
            prog.progress_percent = 20
        elif "Cinematographer" in message or "Keyframe" in message:
            prog.status = GenerationStatus.GENERATING_ASSETS
            prog.current_stage = "Generating Assets"
            prog.progress_percent = 50
        elif "Veo" in message:
            prog.status = GenerationStatus.CREATING_VEO
            prog.current_stage = "Creating Veo Instructions"
            prog.progress_percent = 80
        elif "SEO" in message:
            prog.status = GenerationStatus.GENERATING_SEO
            prog.current_stage = "Generating SEO Metadata"
            prog.progress_percent = 90
            
        await self.manager.broadcast(prog)

# API Endpoints

@app.get("/api/config", response_model=ConfigResponse)
async def get_config():
    """Load current configuration from files."""
    try:
        leader_outfit = PromptLoader.load("leader_outfit.txt")
        follower_outfit = PromptLoader.load("follower_outfit.txt")
        setting = PromptLoader.load("setting.txt")
        
        # Metadata config is YAML-like, let's parse it simply
        meta_content = PromptLoader.load("metadata_config.txt")
        meta_lang = "Spanish"
        meta_keywords = []
        for line in meta_content.splitlines():
            if line.startswith("language:"):
                meta_lang = line.split(":", 1)[1].strip()
            if line.startswith("target_keywords:"):
                meta_keywords = [k.strip() for k in line.split(":", 1)[1].split(",")]

        # List reference poses
        ref_images = []
        for f in PROMPTS_DIR.iterdir():
            if f.suffix.lower() in [".png", ".jpg", ".jpeg"] and "reference_pose" in f.name:
                ref_images.append(f.name)
        
        return ConfigResponse(
            leader_outfit=leader_outfit,
            follower_outfit=follower_outfit,
            setting=setting,
            metadata_language=meta_lang,
            target_keywords=meta_keywords,
            scene_variety=Config.SCENE_VARIETY,
            reference_poses=sorted(ref_images)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
async def update_config(req: ConfigRequest):
    """Update configuration files."""
    try:
        if req.leader_outfit:
            with open(PROMPTS_DIR / "leader_outfit.txt", "w") as f:
                f.write(req.leader_outfit)
        if req.follower_outfit:
            with open(PROMPTS_DIR / "follower_outfit.txt", "w") as f:
                f.write(req.follower_outfit)
        if req.setting:
            with open(PROMPTS_DIR / "setting.txt", "w") as f:
                f.write(req.setting)
        if req.scene_variety is not None:
            # This is in environment, so we'd need to update .env or just the class
            Config.SCENE_VARIETY = req.scene_variety
            
        # Update metadata config
        if req.metadata_language or req.target_keywords:
            meta_content = f"# Metadata Configuration\n\nlanguage: {req.metadata_language or 'Spanish'}\ntarget_keywords: {', '.join(req.target_keywords) if req.target_keywords else ''}\n"
            with open(PROMPTS_DIR / "metadata_config.txt", "w") as f:
                f.write(meta_content)
                
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await progress_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        progress_manager.disconnect(websocket)

async def run_generation_task(req: GenerateSingleRequest):
    """Background task to run video generation."""
    loop = asyncio.get_event_loop()
    # Add our web handler to the central logger
    handler = WebLogHandler(loop, progress_manager)
    logging.getLogger("dance_loop_gen").addHandler(handler)
    
    try:
        director, cinematographer, veo, seo_specialist, _ = get_services()
        user_request = req.user_request or PromptLoader.load("default_user_request.txt")
        
        # Start progress
        await progress_manager.broadcast(GenerationProgress(
            status=GenerationStatus.PLANNING,
            message="Starting generation sequence...",
            progress_percent=10,
            current_stage="Initializing"
        ))
        
        # Run process (sync call to existing logic)
        output_dir = VideoProcessor.process(
            user_request,
            director,
            cinematographer,
            veo,
            seo_specialist,
            reference_pose_index=req.reference_pose_index
        )
        
        # Mark complete
        res_dir = Path(output_dir)
        keyframes = []
        for f in res_dir.iterdir():
            if f.suffix == ".png" and "keyframe" in f.name:
                keyframes.append(KeyframeAsset(
                    scene=f.stem.split("_")[-1].upper(),
                    filename=f.name,
                    url=f"/api/outputs/file/{res_dir.name}/{f.name}"
                ))
        
        await progress_manager.broadcast(GenerationProgress(
            status=GenerationStatus.COMPLETE,
            message="Generation finished successfully!",
            progress_percent=100,
            current_stage="Complete",
            plan_title=res_dir.name,
            keyframes=sorted(keyframes, key=lambda x: x.scene)
        ))
        
    except Exception as e:
        await progress_manager.broadcast(GenerationProgress(
            status=GenerationStatus.ERROR,
            message=f"Error during generation: {str(e)}",
            progress_percent=0,
            current_stage="Error"
        ))
    finally:
        logging.getLogger("dance_loop_gen").removeHandler(handler)

@app.post("/api/generate/single")
async def generate_single(req: GenerateSingleRequest, background_tasks: BackgroundTasks):
    """Start single video generation."""
    if progress_manager.current_progress.status not in [GenerationStatus.IDLE, GenerationStatus.COMPLETE, GenerationStatus.ERROR]:
        raise HTTPException(status_code=400, detail="A generation task is already running.")
        
    background_tasks.add_task(run_generation_task, req)
    return {"status": "started"}

@app.get("/api/outputs", response_model=List[OutputRun])
async def list_outputs():
    """List completed generation runs."""
    runs = []
    if not OUTPUT_DIR.exists():
        return []
        
    for d in sorted(OUTPUT_DIR.iterdir(), key=os.path.getmtime, reverse=True):
        if d.is_dir():
            # Look for a thumbnail (keyframe A)
            thumb = None
            for f in d.iterdir():
                if "keyframe_a" in f.name.lower():
                    thumb = f"/api/outputs/file/{d.name}/{f.name}"
                    break
            
            runs.append(OutputRun(
                run_id=d.name,
                title=d.name.replace("_", " ").title(),
                timestamp=datetime.fromtimestamp(d.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                output_dir=str(d),
                thumbnail_url=thumb
            ))
    return runs

@app.get("/api/outputs/file/{run_id}/{filename}")
async def get_output_file(run_id: str, filename: str):
    """Serve a file from an output directory."""
    file_path = OUTPUT_DIR / run_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

@app.get("/api/prompts/file/{filename}")
async def get_prompt_file(filename: str):
    """Serve a reference image from prompts directory."""
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)

# Static files mount
app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
