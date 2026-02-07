"""
CHRONICLE Response Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MissionStatusEnum(str, Enum):
    """Possible mission states."""
    PENDING = "pending"
    PLANNING = "planning"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    SCORING = "scoring"
    CORRECTING = "correcting"
    EXPORTING = "exporting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Finding(BaseModel):
    """A single research finding."""
    id: str
    name: str
    description: str
    data: Dict[str, Any] = Field(default_factory=dict)
    sources: List[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    verified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class ActionResult(BaseModel):
    """Result of an action taken by the agent."""
    id: str
    action_type: str  # export, email, webhook
    status: str  # success, failed, pending
    details: Dict[str, Any] = Field(default_factory=dict)
    file_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MissionProgress(BaseModel):
    """Progress information for a mission."""
    total_steps: int = 0
    completed_steps: int = 0
    current_phase: str = "initializing"
    findings_count: int = 0
    target_count: int = 10
    quality_average: float = 0.0
    corrections_made: int = 0


class MissionStatus(BaseModel):
    """Current status of a mission."""
    mission_id: str
    status: MissionStatusEnum
    progress: MissionProgress
    current_activity: str = "Initializing..."
    started_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None


class MissionResponse(BaseModel):
    """Response when starting a new mission."""
    mission_id: str
    status: MissionStatusEnum
    message: str
    stream_url: str
    started_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "mission_id": "chr_abc123",
                "status": "planning",
                "message": "Mission started successfully",
                "stream_url": "/api/status/chr_abc123/stream",
                "started_at": "2025-01-15T10:30:00Z"
            }
        }


class StreamEventType(str, Enum):
    """Types of SSE events."""
    STATUS = "status"
    PROGRESS = "progress"
    FINDING = "finding"
    ACTION = "action"
    ERROR = "error"
    COMPLETE = "complete"
    HEARTBEAT = "heartbeat"


class StreamEvent(BaseModel):
    """Server-Sent Event payload."""
    type: StreamEventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
