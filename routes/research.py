"""
CHRONICLE Research Routes - Start and manage research missions
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import asyncio

from models import ResearchRequest, MissionResponse, Mission, MissionState
from models.responses import MissionStatusEnum
from persistence import mission_store
from services.mission_manager import MissionManager

router = APIRouter()

# Global mission manager instance
mission_manager = MissionManager()


@router.post("/research", response_model=MissionResponse)
async def start_research(request: ResearchRequest, background_tasks: BackgroundTasks):
    """
    Start a new research mission.

    The mission will run autonomously, researching the goal and producing
    deliverables like CSV exports, reports, and notifications.
    """
    # Create mission
    mission = Mission(
        goal=request.goal,
        criteria=request.criteria.model_dump(),
        actions_config=request.actions.model_dump(),
        settings=request.settings.model_dump()
    )

    # Save to store
    await mission_store.save(mission)

    # Start mission in background (pass user's API key if provided)
    background_tasks.add_task(mission_manager.run_mission, mission.id, request.api_key)

    return MissionResponse(
        mission_id=mission.id,
        status=MissionStatusEnum.PLANNING,
        message="Mission started successfully. Research will begin shortly.",
        stream_url=f"/api/status/{mission.id}/stream",
        started_at=mission.created_at
    )


@router.get("/research/{mission_id}")
async def get_mission(mission_id: str):
    """Get details of a specific mission."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    return {
        "mission_id": mission.id,
        "goal": mission.goal,
        "state": mission.state.value,
        "current_activity": mission.current_activity,
        "findings_count": len(mission.findings),
        "actions_count": len(mission.actions_completed),
        "created_at": mission.created_at,
        "updated_at": mission.updated_at
    }


@router.delete("/research/{mission_id}")
async def cancel_mission(mission_id: str):
    """Cancel a running mission."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    mission.update_state(MissionState.FAILED, "Mission cancelled by user")
    await mission_store.save(mission)

    return {"mission_id": mission_id, "status": "cancelled", "message": "Mission cancelled"}


@router.get("/research")
async def list_missions(limit: int = 10, offset: int = 0):
    """List all missions."""
    missions = await mission_store.list_all(limit=limit, offset=offset)
    return {
        "missions": [
            {
                "mission_id": m.id,
                "goal": m.goal[:100] + "..." if len(m.goal) > 100 else m.goal,
                "state": m.state.value,
                "findings_count": len(m.findings),
                "created_at": m.created_at
            }
            for m in missions
        ],
        "total": len(missions),
        "limit": limit,
        "offset": offset
    }
