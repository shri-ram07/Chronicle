"""
CHRONICLE - Marathon Research-to-Action Agent
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import settings
from routes import research, status, control, export, findings

# Create FastAPI app
app = FastAPI(
    title="CHRONICLE",
    description="Marathon Research-to-Action Agent - Autonomous multi-day research with real deliverables",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research.router, prefix="/api", tags=["Research"])
app.include_router(status.router, prefix="/api", tags=["Status"])
app.include_router(control.router, prefix="/api", tags=["Control"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(findings.router, prefix="/api", tags=["Findings"])

# Ensure export directory exists
export_dir = Path(settings.export_dir)
export_dir.mkdir(parents=True, exist_ok=True)

# Mount static files for exports
app.mount("/exports", StaticFiles(directory=str(export_dir)), name="exports")

# Data directory
data_dir = Path("./data")
data_dir.mkdir(parents=True, exist_ok=True)


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("=" * 50)
    print("CHRONICLE - Marathon Research-to-Action Agent")
    print("=" * 50)
    print(f"Export directory: {export_dir.absolute()}")
    print(f"Data directory: {data_dir.absolute()}")
    print(f"Server running on http://{settings.host}:{settings.port}")
    print("=" * 50)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "CHRONICLE",
        "description": "Marathon Research-to-Action Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "research": "/api/research",
            "status": "/api/status/{mission_id}",
            "stream": "/api/status/{mission_id}/stream",
            "findings": "/api/findings/{mission_id}",
            "control": "/api/control/{mission_id}",
            "export": "/api/export/{mission_id}"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chronicle"}
