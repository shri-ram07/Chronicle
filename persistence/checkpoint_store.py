"""
CHRONICLE Checkpoint Store - Persistence for pause/resume checkpoints
"""
import json
import aiofiles
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from models.domain import Checkpoint, MissionState


class CheckpointStore:
    """Store and retrieve checkpoints for pause/resume functionality."""

    def __init__(self, data_dir: str = "./data/checkpoints"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_mission_dir(self, mission_id: str) -> Path:
        """Get directory for mission checkpoints."""
        path = self.data_dir / mission_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _get_path(self, mission_id: str, checkpoint_id: str) -> Path:
        """Get file path for a checkpoint."""
        return self._get_mission_dir(mission_id) / f"{checkpoint_id}.json"

    async def save(self, checkpoint: Checkpoint) -> None:
        """Save a checkpoint to storage."""
        path = self._get_path(checkpoint.mission_id, checkpoint.id)
        data = checkpoint.model_dump(mode="json")

        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(data, indent=2, default=str))

    async def get(self, mission_id: str, checkpoint_id: str) -> Optional[Checkpoint]:
        """Get a specific checkpoint."""
        path = self._get_path(mission_id, checkpoint_id)
        if not path.exists():
            return None

        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                data = json.loads(content)

                # Convert state string back to enum
                if "state" in data and isinstance(data["state"], str):
                    data["state"] = MissionState(data["state"])

                return Checkpoint(**data)
        except Exception as e:
            print(f"Error loading checkpoint: {e}")
            return None

    async def get_latest(self, mission_id: str) -> Optional[Checkpoint]:
        """Get the most recent checkpoint for a mission."""
        mission_dir = self._get_mission_dir(mission_id)

        # Get all checkpoint files sorted by modification time
        files = sorted(mission_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

        if not files:
            return None

        checkpoint_id = files[0].stem
        return await self.get(mission_id, checkpoint_id)

    async def list_for_mission(self, mission_id: str) -> List[Checkpoint]:
        """List all checkpoints for a mission."""
        mission_dir = self._get_mission_dir(mission_id)
        checkpoints = []

        for path in sorted(mission_dir.glob("*.json"), reverse=True):
            checkpoint = await self.get(mission_id, path.stem)
            if checkpoint:
                checkpoints.append(checkpoint)

        return checkpoints

    async def delete(self, mission_id: str, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        path = self._get_path(mission_id, checkpoint_id)
        if path.exists():
            path.unlink()
            return True
        return False

    async def delete_all_for_mission(self, mission_id: str) -> int:
        """Delete all checkpoints for a mission."""
        mission_dir = self._get_mission_dir(mission_id)
        count = 0

        for path in mission_dir.glob("*.json"):
            path.unlink()
            count += 1

        return count


# Global instance
checkpoint_store = CheckpointStore()
