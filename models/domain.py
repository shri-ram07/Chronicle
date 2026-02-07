"""
CHRONICLE Domain Models
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


class MissionState(str, Enum):
    """Internal mission states for the agent pipeline."""
    CREATED = "created"
    PLANNING = "planning"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    SCORING = "scoring"
    CORRECTING = "correcting"
    EXPORTING = "exporting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchPhase(str, Enum):
    """Phases of deep research."""
    DISCOVERY = "discovery"      # Find entities with multiple queries
    DEEP_DIVE = "deep_dive"      # Research each entity thoroughly (5+ queries each)
    COMPARISON = "comparison"    # Compare entities against each other
    VALIDATION = "validation"    # Verify claims with sources
    SYNTHESIS = "synthesis"      # Generate final insights


class ResearchDepth(str, Enum):
    """Depth levels for research."""
    SHALLOW = "shallow"          # Current behavior (~1 min)
    MODERATE = "moderate"        # 2-3 queries per entity (~15 min)
    DEEP = "deep"                # 5+ queries per entity (~30 min)
    EXHAUSTIVE = "exhaustive"    # Until quality threshold met (~60 min)


class DeepFinding(BaseModel):
    """A deeply researched entity with rich attributes."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str
    category: str = ""
    description: str = ""

    # Rich attributes (15+ targets)
    pricing: Optional[Dict[str, Any]] = None        # {tiers, monthly, annual, free_trial}
    features: List[str] = Field(default_factory=list)
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list)
    target_audience: str = ""
    competitors: List[str] = Field(default_factory=list)
    website: Optional[str] = None
    founded: Optional[str] = None
    funding: Optional[str] = None
    integrations: List[str] = Field(default_factory=list)
    reviews_summary: str = ""

    # Comparison data
    comparison_notes: Dict[str, str] = Field(default_factory=dict)  # {competitor_name: comparison}

    # Quality tracking
    attribute_count: int = 0
    depth_score: float = 0.0              # 0-1 semantic evaluation
    source_count: int = 0
    sources: List[str] = Field(default_factory=list)  # URLs/references
    research_iterations: int = 0
    research_queries: List[str] = Field(default_factory=list)  # Queries used to research this

    # Timestamps
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    last_deepened: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for storage/export."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "pricing": self.pricing,
            "features": self.features,
            "pros": self.pros,
            "cons": self.cons,
            "use_cases": self.use_cases,
            "target_audience": self.target_audience,
            "competitors": self.competitors,
            "website": self.website,
            "founded": self.founded,
            "funding": self.funding,
            "integrations": self.integrations,
            "reviews_summary": self.reviews_summary,
            "comparison_notes": self.comparison_notes,
            "attribute_count": self.attribute_count,
            "depth_score": self.depth_score,
            "source_count": self.source_count,
            "sources": self.sources,
            "research_iterations": self.research_iterations,
            "quality_score": self.depth_score,  # Alias for compatibility
            "verified": self.depth_score >= 0.7,
        }


class ResearchTask(BaseModel):
    """A single research task in the plan."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    query: str
    priority: int = 1
    status: str = "pending"
    results: List[Dict[str, Any]] = Field(default_factory=list)


class ResearchPlan(BaseModel):
    """The research plan created by the Planner agent."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    goal: str
    strategy: str
    tasks: List[ResearchTask] = Field(default_factory=list)
    estimated_duration_minutes: int = 60
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator('tasks', mode='before')
    @classmethod
    def convert_tasks(cls, v):
        """Convert dict tasks to ResearchTask objects."""
        if not v:
            return []
        result = []
        for task in v:
            if isinstance(task, ResearchTask):
                result.append(task)
            elif isinstance(task, dict):
                result.append(ResearchTask(**task))
            elif isinstance(task, str):
                result.append(ResearchTask(query=task))
            else:
                # Convert any unknown type to string and create a ResearchTask
                result.append(ResearchTask(query=str(task)))
        return result


class Checkpoint(BaseModel):
    """Checkpoint for pause/resume functionality."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    mission_id: str
    state: MissionState
    plan: Optional[ResearchPlan] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    actions_completed: List[str] = Field(default_factory=list)
    current_task_index: int = 0
    thought_signature: Optional[str] = None  # Gemini thought signature for continuity
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Mission(BaseModel):
    """Complete mission object."""
    id: str = Field(default_factory=lambda: f"chr_{uuid.uuid4().hex[:8]}")
    goal: str
    criteria: Dict[str, Any] = Field(default_factory=dict)
    actions_config: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)

    # State
    state: MissionState = MissionState.CREATED
    current_activity: str = "Initializing..."

    # Plan and findings
    plan: Optional[ResearchPlan] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    actions_completed: List[Dict[str, Any]] = Field(default_factory=list)

    # Synthesis report (comprehensive analysis from LLM)
    synthesis: Optional[Dict[str, Any]] = None

    @field_validator('plan', mode='before')
    @classmethod
    def convert_plan(cls, v):
        """Convert dict plan to ResearchPlan object."""
        if v is None:
            return None
        if isinstance(v, ResearchPlan):
            return v
        if isinstance(v, dict):
            try:
                # Handle tasks that might be strings or dicts
                tasks = v.get('tasks', [])
                converted_tasks = []
                for task in tasks:
                    if isinstance(task, str):
                        converted_tasks.append({'query': task})
                    elif isinstance(task, dict):
                        converted_tasks.append(task)
                    else:
                        # Convert unknown types to string query
                        converted_tasks.append({'query': str(task)})
                v['tasks'] = converted_tasks

                # Ensure goal is present (required by ResearchPlan)
                if 'goal' not in v:
                    v['goal'] = v.get('strategy', 'Research task')[:200]

                return ResearchPlan(**v)
            except Exception as e:
                print(f"Error converting plan dict to ResearchPlan: {e}")
                # Return a minimal valid ResearchPlan
                return ResearchPlan(
                    goal=v.get('strategy', 'Research task')[:200],
                    strategy=v.get('strategy', 'Direct research'),
                    tasks=[],
                    estimated_duration_minutes=v.get('estimated_duration_minutes', 30)
                )
        # For any other type, return None
        return None

    # Progress tracking
    total_steps: int = 0
    completed_steps: int = 0
    corrections_made: int = 0

    # Thought signature for marathon continuity
    thought_signature: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def update_state(self, new_state: MissionState, activity: str = None):
        """Update mission state and activity."""
        self.state = new_state
        if activity:
            self.current_activity = activity
        self.updated_at = datetime.utcnow()

    def add_finding(self, finding: Dict[str, Any]):
        """Add a new finding to the mission."""
        self.findings.append(finding)
        self.updated_at = datetime.utcnow()

    def add_action(self, action: Dict[str, Any]):
        """Record a completed action."""
        self.actions_completed.append(action)
        self.updated_at = datetime.utcnow()

    def to_checkpoint(self) -> Checkpoint:
        """Create a checkpoint from current state."""
        return Checkpoint(
            mission_id=self.id,
            state=self.state,
            plan=self.plan,
            findings=self.findings.copy(),
            actions_completed=[a.get("id", "") for a in self.actions_completed],
            current_task_index=self.completed_steps,
            thought_signature=self.thought_signature
        )
