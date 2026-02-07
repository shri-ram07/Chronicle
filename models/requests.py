"""
CHRONICLE Request Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ResearchCriteria(BaseModel):
    """Criteria for evaluating research findings."""
    minimum_funding: Optional[int] = None
    required_fields: List[str] = Field(default_factory=lambda: ["name", "description"])
    geographic_focus: Optional[List[str]] = None
    quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_results: int = Field(default=10, ge=1, le=100)


class ActionConfig(BaseModel):
    """Configuration for actions to take on completion."""
    export_formats: List[str] = Field(default_factory=lambda: ["json", "csv"])
    email_notification: Optional[str] = None
    webhook_url: Optional[str] = None


class MissionSettings(BaseModel):
    """Settings for mission execution."""
    max_duration_hours: int = Field(default=4, ge=1, le=24)
    checkpoint_interval_minutes: int = Field(default=15, ge=5, le=60)
    auto_export: bool = True


class ResearchRequest(BaseModel):
    """Request to start a new research mission."""
    goal: str = Field(..., min_length=10, description="The research goal to achieve")

    # User-provided API key (required for public deployment)
    api_key: Optional[str] = Field(
        default=None,
        description="User's Gemini API key for this request"
    )

    # NEW: Research depth control
    depth: str = Field(
        default="deep",
        description="Research depth: shallow (~1min), moderate (~15min), deep (~30min), exhaustive (~60min)"
    )
    target_findings: int = Field(
        default=15,
        ge=5, le=50,
        description="Target number of deeply researched entities (quality over quantity)"
    )

    criteria: ResearchCriteria = Field(default_factory=ResearchCriteria)
    actions: ActionConfig = Field(default_factory=ActionConfig)
    settings: MissionSettings = Field(default_factory=MissionSettings)

    class Config:
        json_schema_extra = {
            "example": {
                "goal": "Find the best project management tools for remote teams",
                "depth": "deep",
                "target_findings": 15,
                "criteria": {
                    "required_fields": ["name", "description", "pricing", "features"],
                    "quality_threshold": 0.7,
                    "max_results": 15
                },
                "actions": {
                    "export_formats": ["json", "md", "pdf"],
                    "email_notification": "user@example.com"
                },
                "settings": {
                    "max_duration_hours": 1,
                    "checkpoint_interval_minutes": 15
                }
            }
        }


class ExportRequest(BaseModel):
    """Request to export mission findings."""
    formats: List[str] = Field(default_factory=lambda: ["json", "csv"])
    include_metadata: bool = True
    filename_prefix: Optional[str] = None
