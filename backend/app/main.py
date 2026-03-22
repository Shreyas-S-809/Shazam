"""Song Shazam Pro — FastAPI application entry point."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import HealthResponse
from app.routers import audio, links

load_dotenv()

app = FastAPI(
    title="Song Shazam Pro API",
    description="AI-powered song recognition, spectrogram generation, and music link aggregation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────

app.include_router(audio.router, prefix="/api/audio", tags=["Audio"])
app.include_router(links.router, prefix="/api/links", tags=["Links"])


# ── Health check ─────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()
