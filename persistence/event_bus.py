"""
CHRONICLE Event Bus - Real-time event streaming for SSE
"""
import asyncio
from typing import AsyncIterator, Dict, List, Any
from datetime import datetime
from collections import defaultdict

from models.responses import StreamEvent, StreamEventType


class EventBus:
    """
    Event bus for real-time mission event streaming.

    Supports multiple subscribers per mission and maintains
    an event history for late joiners.
    """

    def __init__(self, history_limit: int = 100):
        self._subscribers: Dict[str, List[asyncio.Queue]] = defaultdict(list)
        self._history: Dict[str, List[StreamEvent]] = defaultdict(list)
        self._history_limit = history_limit

    async def publish(self, mission_id: str, event: StreamEvent) -> None:
        """
        Publish an event to all subscribers of a mission.

        Args:
            mission_id: The mission ID to publish to
            event: The event to publish
        """
        # Add to history
        self._history[mission_id].append(event)

        # Trim history if needed
        if len(self._history[mission_id]) > self._history_limit:
            self._history[mission_id] = self._history[mission_id][-self._history_limit:]

        # Notify all subscribers
        for queue in self._subscribers[mission_id]:
            try:
                await queue.put(event)
            except Exception as e:
                print(f"Error publishing event: {e}")

    async def subscribe(self, mission_id: str) -> AsyncIterator[StreamEvent]:
        """
        Subscribe to events for a mission.

        Yields events as they are published. Includes a heartbeat
        every 30 seconds to keep the connection alive.

        Args:
            mission_id: The mission ID to subscribe to

        Yields:
            StreamEvent objects as they are published
        """
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[mission_id].append(queue)

        try:
            while True:
                try:
                    # Wait for event with timeout for heartbeat
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield StreamEvent(
                        type=StreamEventType.HEARTBEAT,
                        data={"timestamp": datetime.utcnow().isoformat()}
                    )
        finally:
            # Clean up subscriber
            if queue in self._subscribers[mission_id]:
                self._subscribers[mission_id].remove(queue)

    async def get_history(self, mission_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get event history for a mission.

        Args:
            mission_id: The mission ID
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """
        events = self._history.get(mission_id, [])[-limit:]
        return [
            {
                "type": e.type.value,
                "data": e.data,
                "timestamp": e.timestamp.isoformat()
            }
            for e in events
        ]

    def clear_history(self, mission_id: str) -> None:
        """Clear event history for a mission."""
        if mission_id in self._history:
            del self._history[mission_id]

    # Convenience methods for publishing specific event types

    async def emit_status(self, mission_id: str, state: str, activity: str) -> None:
        """Emit a status change event."""
        await self.publish(mission_id, StreamEvent(
            type=StreamEventType.STATUS,
            data={"state": state, "activity": activity}
        ))

    async def emit_progress(self, mission_id: str, completed: int, total: int, phase: str) -> None:
        """Emit a progress update event."""
        await self.publish(mission_id, StreamEvent(
            type=StreamEventType.PROGRESS,
            data={
                "completed": completed,
                "total": total,
                "phase": phase,
                "percentage": (completed / total * 100) if total > 0 else 0
            }
        ))

    async def emit_finding(self, mission_id: str, finding: Dict[str, Any]) -> None:
        """Emit a new finding event."""
        await self.publish(mission_id, StreamEvent(
            type=StreamEventType.FINDING,
            data=finding
        ))

    async def emit_action(self, mission_id: str, action: Dict[str, Any]) -> None:
        """Emit an action completed event."""
        await self.publish(mission_id, StreamEvent(
            type=StreamEventType.ACTION,
            data=action
        ))

    async def emit_error(self, mission_id: str, error: str, details: Dict[str, Any] = None) -> None:
        """Emit an error event."""
        await self.publish(mission_id, StreamEvent(
            type=StreamEventType.ERROR,
            data={"error": error, "details": details or {}}
        ))

    async def emit_complete(self, mission_id: str, summary: Dict[str, Any]) -> None:
        """Emit a mission complete event."""
        await self.publish(mission_id, StreamEvent(
            type=StreamEventType.COMPLETE,
            data=summary
        ))


# Global instance
event_bus = EventBus()
