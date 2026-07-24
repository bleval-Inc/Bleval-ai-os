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
from axiom.runtime.lifecycle import AxiomRuntime

# Global runtime instance
runtime = AxiomRuntime()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan: bootstrap on startup, shutdown on exit."""
    # Startup
    await runtime.start()
    set_runtime(runtime)
    yield
    # Shutdown
    await runtime.shutdown()


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


@app.get("/")
async def root():
    """Root endpoint — system information."""
    return {
        "service": "Axiom OS",
        "version": __version__,
        "status": "running" if runtime.is_running else "initialising",
        "docs": "/docs",
    }