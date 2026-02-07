"""
CHRONICLE Configuration Settings
"""
# Force load .env file FIRST, overriding any system environment variables
from dotenv import load_dotenv
load_dotenv(override=True)

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Gemini API (optional - users can provide their own key in requests)
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")

    # Model Configuration - Using Gemini 3 Flash (latest)
    coordinator_model: str = "gemini-3-flash"
    planner_model: str = "gemini-3-flash"
    researcher_model: str = "gemini-3-flash"
    analyst_model: str = "gemini-3-flash"
    scorer_model: str = "gemini-3-flash"
    actioner_model: str = "gemini-3-flash"

    # Server Configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=True, alias="DEBUG")

    # Export Configuration
    export_dir: Path = Field(default=Path("./exports"), alias="EXPORT_DIR")

    # Mission Configuration
    max_mission_duration_hours: int = 24
    checkpoint_interval_minutes: int = 15
    max_iterations_per_phase: int = 10
    quality_threshold: float = 0.8

    # ===========================================
    # DEEP RESEARCH CONFIGURATION
    # ===========================================

    # Research depth: shallow|moderate|deep|exhaustive
    research_depth: str = Field(default="deep", alias="RESEARCH_DEPTH")

    # Discovery Phase - Find entities with multiple search queries
    discovery_queries: int = 5              # Number of search angles per goal
    target_entities: int = 15               # Quality over quantity (was 100+)

    # Deep Dive Phase - THE KEY CHANGE: Multiple queries per entity
    deepdive_queries_per_entity: int = 5    # 5 queries per entity!
    min_attributes_per_entity: int = 10     # Minimum required attributes

    # Comparison Phase
    comparison_pairs: int = 10              # Number of entity comparisons

    # Validation Phase
    validation_queries_per_entity: int = 2  # Verify key claims

    # Time Management - Don't finish too fast!
    min_research_duration_minutes: int = 10   # Minimum time for "deep" research
    max_research_duration_minutes: int = 60   # Cap duration
    delay_between_queries_seconds: float = 1.0  # Rate limiting

    # Quality Thresholds for Semantic Scoring
    depth_score_threshold: float = 0.6      # Minimum depth score to pass
    max_deepening_iterations: int = 3       # Re-research attempts for shallow findings

    # Web Search - ENABLE for real-time data
    enable_google_search: bool = True       # Enable Gemini Google Search grounding

    # Optional Google Cloud
    google_cloud_project: Optional[str] = Field(default=None, alias="GOOGLE_CLOUD_PROJECT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
