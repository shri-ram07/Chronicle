"""
CHRONICLE Status Routes - Real-time status and SSE streaming
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from datetime import datetime

from models import MissionStatus, StreamEvent
from models.responses import MissionStatusEnum, MissionProgress, StreamEventType
from persistence import mission_store, event_bus

router = APIRouter()


@router.get("/status/{mission_id}")
async def get_status(mission_id: str) -> MissionStatus:
    """Get current status of a mission."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    # Calculate progress
    target_count = mission.criteria.get("max_results", 10)
    findings_count = len(mission.findings)
    quality_scores = [f.get("quality_score", 0) for f in mission.findings if f.get("quality_score")]
    quality_avg = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    progress = MissionProgress(
        total_steps=mission.total_steps,
        completed_steps=mission.completed_steps,
        current_phase=mission.state.value,
        findings_count=findings_count,
        target_count=target_count,
        quality_average=quality_avg,
        corrections_made=mission.corrections_made
    )

    # Map internal state to API status
    status_map = {
        "created": MissionStatusEnum.PENDING,
        "planning": MissionStatusEnum.PLANNING,
        "researching": MissionStatusEnum.RESEARCHING,
        "analyzing": MissionStatusEnum.ANALYZING,
        "scoring": MissionStatusEnum.SCORING,
        "correcting": MissionStatusEnum.CORRECTING,
        "exporting": MissionStatusEnum.EXPORTING,
        "paused": MissionStatusEnum.PAUSED,
        "completed": MissionStatusEnum.COMPLETED,
        "failed": MissionStatusEnum.FAILED
    }

    return MissionStatus(
        mission_id=mission.id,
        status=status_map.get(mission.state.value, MissionStatusEnum.PENDING),
        progress=progress,
        current_activity=mission.current_activity,
        started_at=mission.created_at,
        updated_at=mission.updated_at
    )


@router.get("/status/{mission_id}/stream")
async def stream_status(mission_id: str):
    """
    Stream real-time status updates via Server-Sent Events (SSE).

    Events include:
    - status: Mission state changes
    - progress: Progress updates
    - finding: New finding discovered
    - action: Action completed (export, email, etc.)
    - error: Error occurred
    - complete: Mission completed
    """
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    async def event_generator():
        """Generate SSE events for the mission."""
        # Send initial status
        initial_event = StreamEvent(
            type=StreamEventType.STATUS,
            data={
                "mission_id": mission_id,
                "state": mission.state.value,
                "activity": mission.current_activity,
                "findings_count": len(mission.findings)
            }
        )
        yield {
            "event": initial_event.type.value,
            "data": json.dumps(initial_event.data, default=str)
        }

        # Subscribe to mission events
        async for event in event_bus.subscribe(mission_id):
            yield {
                "event": event.type.value,
                "data": json.dumps(event.data, default=str)
            }

            # Stop streaming if mission is complete
            if event.type in [StreamEventType.COMPLETE, StreamEventType.ERROR]:
                break

        # Final heartbeat
        yield {
            "event": "heartbeat",
            "data": json.dumps({"status": "stream_ended"})
        }

    return EventSourceResponse(event_generator())


@router.get("/status/{mission_id}/activity")
async def get_activity_log(mission_id: str, limit: int = 50):
    """Get recent activity log for a mission."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    # Get activity log from event bus
    activities = await event_bus.get_history(mission_id, limit=limit)

    return {
        "mission_id": mission_id,
        "activities": activities,
        "count": len(activities)
    }
