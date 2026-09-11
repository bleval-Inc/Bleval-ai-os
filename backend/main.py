"""Axiom OS — FastAPI Application Entry Point.

Start the server:
    uvicorn main:app --reload --port 8000
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from axiom import __version__
from axiom.api.routes import router as api_router, set_runtime
from axiom.api.routes_journal import router as journal_router
from axiom.api.routes_intelligence import router as intelligence_router, set_runtime as set_intelligence_runtime
from axiom.runtime.lifecycle import AxiomRuntime
from voice_pipeline_routes import router as voice_router, set_runtime as set_voice_runtime

# Global runtime instance
runtime = AxiomRuntime()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: bootstrap on startup, shutdown on exit."""
    # Startup
    print("[STARTUP_VOICE] Lifespan startup: about to call runtime.start()")
    await runtime.start()
    print(f"[STARTUP_VOICE] Lifespan startup: runtime.start() completed, runtime id={id(runtime)}, running={runtime._running}")
    set_runtime(runtime)
    set_intelligence_runtime(runtime)
    set_voice_runtime(runtime)
    print(f"[STARTUP_VOICE] Lifespan startup: voice_pipeline set, voice_pipeline id={id(runtime.voice_pipeline) if runtime.voice_pipeline else None}")
    yield
    # Shutdown
    print("[STARTUP_VOICE] Lifespan shutdown: about to call runtime.shutdown()")
    await runtime.shutdown()
    print("[STARTUP_VOICE] Lifespan shutdown: runtime.shutdown() completed")


app = FastAPI(
    title="Axiom OS",
    description="AI Operating System — coordinate executives, departments, workflows, and agents",
    version=__version__,
    lifespan=lifespan,
)

# CORS — allow all origins in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router)
app.include_router(journal_router)
app.include_router(intelligence_router)
app.include_router(voice_router)


@app.get("/")
async def root():
    """Root endpoint — system information."""
    return {
        "service": "Axiom OS",
        "version": __version__,
        "status": "running" if runtime.is_running else "initialising",
        "docs": "/docs",
    }
@app.get("/api/v1/debug/voice")
async def debug_voice():
    """Temporary voice pipeline diagnostic endpoint."""
    vp = runtime.voice_pipeline

    if vp is None:
        return {
            "voice_pipeline": False,
            "message": "runtime.voice_pipeline is None",
        }

    # Access wake detector through audio processor
    detector = getattr(vp.audio_processor, 'wake_detector', None) if vp.audio_processor else None
    # Get audio stream from audio processor (not from detector)
    audio_processor = vp.audio_processor
    stream = getattr(audio_processor, '_stream', None) if audio_processor else None
    thread = getattr(detector, "_thread", None) if detector else None
    event_loop = getattr(vp, "_loop", None)

    return {
        "voice_pipeline": True,
        "pipeline_running": getattr(vp, "_running", None),

        "event_loop": {
            "exists": event_loop is not None,
            "running": (
                event_loop.is_running()
                if event_loop is not None
                else False
            ),
            "closed": (
                event_loop.is_closed()
                if event_loop is not None
                else None
            ),
        },

        "detector": {
            "exists": detector is not None,
            "running": getattr(detector, "_running", False) if detector else False,
            "thread_exists": thread is not None,
            "thread_alive": (
                thread.is_alive()
                if thread is not None
                else False
            ),
            "models": list(
                getattr(detector, "_models", {}).keys()
            ) if detector else [],
            "latest_scores": getattr(
                detector,
                "_latest_scores",
                {}
            ) if detector else {},
        },

        "audio_stream": {
            "exists": stream is not None,
            "active": (
                stream.active
                if stream is not None
                else False
            ),
            "closed": (
                stream.closed
                if stream is not None
                else None
            ),
            "device": (
                stream.device
                if stream is not None
                else None
            ),
            "samplerate": (
                stream.samplerate
                if stream is not None
                else None
            ),
            "channels": (
                stream.channels
                if stream is not None
                else None
            ),
        },
    }
