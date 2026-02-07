"""
CHRONICLE Export Routes - Export mission findings
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from models import ExportRequest, Mission
from persistence import mission_store
from tools.file_export import FileExporter

router = APIRouter()
file_exporter = FileExporter()


@router.post("/export/{mission_id}")
async def export_findings(mission_id: str, request: ExportRequest = None):
    """
    Export mission findings to specified formats.

    Supports: json, csv, pdf, markdown
    """
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    if not mission.findings:
        raise HTTPException(
            status_code=400,
            detail="No findings to export. Mission may still be in progress."
        )

    # Use request or defaults
    if request is None:
        request = ExportRequest()

    exports = []
    for format in request.formats:
        try:
            result = await file_exporter.export(
                mission=mission,
                format=format,
                include_metadata=request.include_metadata,
                filename_prefix=request.filename_prefix
            )
            exports.append(result)
        except Exception as e:
            exports.append({
                "format": format,
                "status": "failed",
                "error": str(e)
            })

    return {
        "mission_id": mission_id,
        "exports": exports,
        "total_findings": len(mission.findings),
        "exported_at": datetime.utcnow()
    }


@router.get("/export/{mission_id}/files")
async def list_exports(mission_id: str):
    """List all exported files for a mission."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    # Get exports from actions
    exports = [
        action for action in mission.actions_completed
        if action.get("action_type") == "export"
    ]

    return {
        "mission_id": mission_id,
        "exports": exports,
        "count": len(exports)
    }


@router.get("/export/{mission_id}/download/{filename}")
async def download_export(mission_id: str, filename: str):
    """Download a specific export file."""
    from fastapi.responses import FileResponse
    from pathlib import Path
    from config import settings

    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    file_path = settings.export_dir / mission_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File {filename} not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )
