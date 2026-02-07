"""
CHRONICLE Mission Store - Persistence for missions
Uses local JSON files for simplicity (can upgrade to Firestore later)
"""
import json
import aiofiles
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from models.domain import Mission, MissionState


class MissionStore:
    """Store and retrieve missions using local JSON files."""

    def __init__(self, data_dir: str = "./data/missions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Mission] = {}

    def _get_path(self, mission_id: str) -> Path:
        """Get file path for a mission."""
        return self.data_dir / f"{mission_id}.json"

    async def save(self, mission: Mission) -> None:
        """Save a mission to storage."""
        mission.updated_at = datetime.utcnow()
        self._cache[mission.id] = mission

        path = self._get_path(mission.id)
        # Pydantic v2 with mode="json" handles datetime serialization automatically
        data = mission.model_dump(mode="json")

        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    async def get(self, mission_id: str) -> Optional[Mission]:
        """Get a mission by ID."""
        # Check cache first
        if mission_id in self._cache:
            return self._cache[mission_id]

        path = self._get_path(mission_id)
        if not path.exists():
            return None

        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                data = json.loads(content)

                # Convert state string back to enum
                if "state" in data and isinstance(data["state"], str):
                    data["state"] = MissionState(data["state"])

                mission = Mission(**data)
                self._cache[mission_id] = mission
                return mission
        except Exception as e:
            print(f"Error loading mission {mission_id}: {e}")
            return None

    async def delete(self, mission_id: str) -> bool:
        """Delete a mission."""
        if mission_id in self._cache:
            del self._cache[mission_id]

        path = self._get_path(mission_id)
        if path.exists():
            path.unlink()
            return True
        return False

    async def list_all(self, limit: int = 10, offset: int = 0) -> List[Mission]:
        """List all missions."""
        missions = []

        # Get all JSON files
        files = sorted(self.data_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

        for path in files[offset:offset + limit]:
            mission_id = path.stem
            mission = await self.get(mission_id)
            if mission:
                missions.append(mission)

        return missions

    async def update_state(self, mission_id: str, state: MissionState, activity: str = None) -> Optional[Mission]:
        """Update mission state."""
        mission = await self.get(mission_id)
        if mission:
            mission.update_state(state, activity)
            await self.save(mission)
        return mission

    async def add_finding(self, mission_id: str, finding: dict) -> Optional[Mission]:
        """Add a finding to a mission."""
        mission = await self.get(mission_id)
        if mission:
            mission.add_finding(finding)
            await self.save(mission)
        return mission

    async def add_action(self, mission_id: str, action: dict) -> Optional[Mission]:
        """Record a completed action."""
        mission = await self.get(mission_id)
        if mission:
            mission.add_action(action)
            await self.save(mission)
        return mission


# Global instance
mission_store = MissionStore()
