"""
CHRONICLE Control Routes - Pause, resume, and control missions
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime

from models import Mission, MissionState, Checkpoint
from persistence import mission_store, checkpoint_store

router = APIRouter()


@router.post("/control/{mission_id}/pause")
async def pause_mission(mission_id: str):
    """
    Pause a running mission.

    Creates a checkpoint with the current state and thought signature
    for seamless resume later.
    """
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    if mission.state in [MissionState.COMPLETED, MissionState.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause mission in state: {mission.state.value}"
        )

    if mission.state == MissionState.PAUSED:
        return {
            "mission_id": mission_id,
            "status": "already_paused",
            "message": "Mission is already paused"
        }

    # Create checkpoint
    checkpoint = mission.to_checkpoint()
    await checkpoint_store.save(checkpoint)

    # Update mission state
    mission.update_state(MissionState.PAUSED, "Mission paused by user")
    await mission_store.save(mission)

    return {
        "mission_id": mission_id,
        "status": "paused",
        "checkpoint_id": checkpoint.id,
        "message": "Mission paused. Use /resume to continue.",
        "findings_saved": len(mission.findings),
        "thought_signature_saved": mission.thought_signature is not None
    }


@router.post("/control/{mission_id}/resume")
async def resume_mission(mission_id: str):
    """
    Resume a paused mission.

    Loads the checkpoint and thought signature to continue
    exactly where the mission left off.
    """
    from services.mission_manager import MissionManager

    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    if mission.state != MissionState.PAUSED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume mission in state: {mission.state.value}. Mission must be paused."
        )

    # Load checkpoint
    checkpoint = await checkpoint_store.get_latest(mission_id)
    if not checkpoint:
        raise HTTPException(
            status_code=404,
            detail=f"No checkpoint found for mission {mission_id}"
        )

    # Resume mission
    mission.update_state(MissionState.RESEARCHING, "Resuming mission from checkpoint...")
    await mission_store.save(mission)

    # Start mission manager to continue
    mission_manager = MissionManager()
    import asyncio
    asyncio.create_task(mission_manager.resume_mission(mission_id, checkpoint))

    return {
        "mission_id": mission_id,
        "status": "resuming",
        "checkpoint_id": checkpoint.id,
        "message": "Mission resuming from checkpoint",
        "findings_restored": len(checkpoint.findings),
        "thought_signature_restored": checkpoint.thought_signature is not None
    }


@router.post("/control/{mission_id}/retry")
async def retry_mission(mission_id: str):
    """Retry a failed mission from the beginning."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    if mission.state != MissionState.FAILED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot retry mission in state: {mission.state.value}. Mission must be failed."
        )

    # Reset mission state
    mission.state = MissionState.CREATED
    mission.current_activity = "Retrying mission..."
    mission.findings = []
    mission.actions_completed = []
    mission.completed_steps = 0
    mission.corrections_made = 0
    mission.thought_signature = None
    mission.updated_at = datetime.utcnow()

    await mission_store.save(mission)

    # Start mission
    from services.mission_manager import MissionManager
    import asyncio
    mission_manager = MissionManager()
    asyncio.create_task(mission_manager.run_mission(mission_id))

    return {
        "mission_id": mission_id,
        "status": "retrying",
        "message": "Mission restarted from beginning"
    }
