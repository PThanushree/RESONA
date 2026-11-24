"""
RESONA Web Application Server
FastAPI backend powering accessible editor UI, AST analysis,
runtime debugging trace streaming, audio earcons, and AI narration.
Includes Adaptive Audio Feedback Settings (Deliverable 7) and Context Engine (Phase 4).
"""

from __future__ import annotations
import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from resona.core.ast_analyzer import ASTAnalyzer
from resona.core.runtime_debugger import RuntimeDebugger
from resona.core.sonification_engine import SonificationEngine
from resona.core.ai_narrator import AINarrator
from resona.core.audio_synthesizer import AudioSynthesizer
from resona.core.context_engine import ContextEngine
from resona.core.adaptive_audio import AdaptiveAudioManager, AdaptiveAudioSettings

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
parent1 = os.path.dirname(BASE_DIR)
if os.path.exists(os.path.join(parent1, "examples")):
    PROJECT_DIR = parent1
else:
    PROJECT_DIR = os.path.dirname(parent1)
EXAMPLES_DIR = os.path.join(PROJECT_DIR, "examples")

app = FastAPI(
    title="RESONA Accessible IDE",
    description="Accessible Programming and Audio-Based Code Comprehension System for Blind Programmers",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Core services
ast_analyzer = ASTAnalyzer()
runtime_debugger = RuntimeDebugger()
sonification_engine = SonificationEngine()
ai_narrator = AINarrator()
context_engine = ContextEngine()
audio_manager = AdaptiveAudioManager()
earcon_library = AudioSynthesizer.get_earcon_library()


class CodeRequest(BaseModel):
    code: str
    breakpoints: Optional[List[int]] = None
    active_line: Optional[int] = 1


class AskAIRequest(BaseModel):
    question: str
    code: Optional[str] = None
    line: Optional[int] = 1


class SettingsRequest(BaseModel):
    verbosity_level: Optional[str] = None
    feedback_mode: Optional[str] = None
    earcon_volume: Optional[float] = None
    speech_volume: Optional[float] = None
    speech_rate: Optional[float] = None
    speech_pitch: Optional[float] = None
    indentation_audio: Optional[bool] = None
    stereo_panning: Optional[bool] = None
    variable_chimes: Optional[bool] = None
    soundscape_pace_ms: Optional[int] = None


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(
        content=content,
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.post("/api/pipeline")
def process_pipeline(req: CodeRequest):
    """
    Unified high-performance single-pass pipeline:
    AST Analysis + Scope Resolution + Runtime Execution + Audio Soundscape + Context Engine.
    """
    bp_set = set(req.breakpoints) if req.breakpoints else set()

    # 1. AST Analysis with Scope Resolution
    analysis = ast_analyzer.analyze(req.code)

    # 2. Update Context Engine
    context_engine.update_code(req.code, analysis)
    cursor_ctx = context_engine.get_cursor_context(req.active_line or 1)

    # 3. Runtime Trace & Soundscape
    trace_res = None
    soundscape = []
    runtime_exp = None

    if analysis.is_valid:
        trace_res = runtime_debugger.execute_and_trace(req.code, bp_set)
        context_engine.update_trace(trace_res)
        soundscape = sonification_engine.generate_trace_soundscape(trace_res, analysis.total_lines)
        runtime_exp = ai_narrator.explain_runtime_trace(trace_res, req.code)

    # 4. AI Code Structure Overview
    structure_exp = ai_narrator.explain_code_structure(analysis, req.code)

    return JSONResponse(content={
        "analysis": analysis.to_dict(),
        "trace": trace_res.to_dict() if trace_res else None,
        "soundscape": soundscape,
        "cursor_context": cursor_ctx.to_dict(),
        "settings": audio_manager.settings.to_dict(),
        "narration": {
            "structure": structure_exp,
            "runtime": runtime_exp
        }
    })


@app.post("/api/ask_ai")
def ask_ai(req: AskAIRequest):
    """Interactive AI Coding Assistant for blind programmers (Phase 5)."""
    if req.code:
        analysis = ast_analyzer.analyze(req.code)
        context_engine.update_code(req.code, analysis)
    if req.line:
        context_engine.record_navigation(req.line)

    prompt_context = context_engine.build_llm_prompt_context(req.question)
    result = ai_narrator.ask_ai_assistant(req.question, prompt_context)
    return JSONResponse(content=result)


@app.get("/api/settings")
def get_settings():
    """Retrieve active adaptive audio feedback configuration (Deliverable 7)."""
    return JSONResponse(content=audio_manager.settings.to_dict())


@app.post("/api/settings")
def update_settings(req: SettingsRequest):
    """Update and persist adaptive audio feedback configuration."""
    current = audio_manager.settings.to_dict()
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    current.update(updates)
    new_settings = AdaptiveAudioSettings.from_dict(current)
    audio_manager.save(new_settings)
    return JSONResponse(content=new_settings.to_dict())


@app.post("/api/settings/preset/{preset_name}")
def apply_preset(preset_name: str):
    """Apply standard accessibility preset (beginner, expert, sonification_only, speech_only)."""
    settings = audio_manager.apply_preset(preset_name)
    return JSONResponse(content=settings.to_dict())


@app.post("/api/analyze")
def analyze_code(req: CodeRequest):
    result = ast_analyzer.analyze(req.code)
    return JSONResponse(content=result.to_dict())


@app.post("/api/run")
def run_code(req: CodeRequest):
    bp_set = set(req.breakpoints) if req.breakpoints else set()
    result = runtime_debugger.execute_and_trace(req.code, bp_set)
    return JSONResponse(content=result.to_dict())


@app.post("/api/narrate")
def narrate_code(req: CodeRequest):
    analysis = ast_analyzer.analyze(req.code)
    structure_exp = ai_narrator.explain_code_structure(analysis, req.code)
    runtime_exp = None
    if analysis.is_valid:
        trace_res = runtime_debugger.execute_and_trace(req.code)
        runtime_exp = ai_narrator.explain_runtime_trace(trace_res, req.code)
    return JSONResponse(content={
        "structure": structure_exp,
        "runtime": runtime_exp
    })


@app.get("/api/example/{filename}")
def get_example(filename: str):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(EXAMPLES_DIR, safe_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Example file not found")
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return JSONResponse(content={
        "filename": safe_name,
        "title": safe_name.replace("_", " ").replace(".py", "").title(),
        "code": content
    })


@app.get("/api/audio/{earcon_id}")
def get_earcon_audio(earcon_id: str):
    if earcon_id in earcon_library:
        return Response(content=earcon_library[earcon_id], media_type="audio/wav")
    if earcon_id.startswith("depth_"):
        try:
            depth = int(earcon_id.split("_")[1])
            freq = sonification_engine.get_frequency_for_depth(depth)
            return Response(content=AudioSynthesizer.generate_tone(freq, 70.0, volume=0.35), media_type="audio/wav")
        except ValueError:
            pass
    raise HTTPException(status_code=404, detail="Earcon not found")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "RESONA", "version": "1.0.0"}
