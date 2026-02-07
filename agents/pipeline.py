"""
CHRONICLE Agent Pipeline - Multi-agent orchestration using Google ADK

This is the main agent that coordinates research missions, delegating to
specialized sub-agents for planning, research, analysis, scoring, and actions.
"""
from google import genai
from google.genai import types
from google.adk import Agent
from google.adk.tools import google_search
from typing import Optional, Dict, Any, List
import json

from config import settings


# Initialize Gemini client
client = genai.Client(api_key=settings.gemini_api_key)


def create_chronicle_agent() -> Agent:
    """
    Create the main CHRONICLE agent with all capabilities.

    This agent handles the full research lifecycle:
    1. Planning - Creates research strategy
    2. Researching - Executes web searches
    3. Analyzing - Synthesizes findings
    4. Scoring - Evaluates quality
    5. Acting - Exports results and sends notifications
    """

    # Define custom tools for CHRONICLE

    def create_research_plan(goal: str, criteria: dict) -> dict:
        """
        Create a structured research plan based on the goal and criteria.

        Args:
            goal: The research goal to achieve
            criteria: Criteria for evaluating findings

        Returns:
            A structured research plan with tasks
        """
        # This will be enhanced by the LLM
        return {
            "goal": goal,
            "criteria": criteria,
            "tasks": [],
            "strategy": "comprehensive_search"
        }

    def analyze_finding(raw_data: dict, criteria: dict) -> dict:
        """
        Analyze and structure a raw finding.

        Args:
            raw_data: Raw data from search
            criteria: Evaluation criteria

        Returns:
            Structured finding with quality score
        """
        required_fields = criteria.get("required_fields", [])
        present_fields = [f for f in required_fields if f in raw_data and raw_data[f]]
        completeness = len(present_fields) / len(required_fields) if required_fields else 1.0

        return {
            **raw_data,
            "quality_score": completeness,
            "missing_fields": [f for f in required_fields if f not in present_fields],
            "verified": completeness >= 0.8
        }

    def score_findings(findings: list, criteria: dict) -> dict:
        """
        Score all findings and identify gaps.

        Args:
            findings: List of findings to score
            criteria: Quality criteria

        Returns:
            Scoring results with gaps identified
        """
        threshold = criteria.get("quality_threshold", 0.8)
        scores = [f.get("quality_score", 0) for f in findings]

        low_quality = [f for f in findings if f.get("quality_score", 0) < threshold]
        high_quality = [f for f in findings if f.get("quality_score", 0) >= threshold]

        return {
            "total_findings": len(findings),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "high_quality_count": len(high_quality),
            "low_quality_count": len(low_quality),
            "needs_correction": len(low_quality) > 0,
            "gaps": [
                {
                    "finding_id": f.get("id"),
                    "missing_fields": f.get("missing_fields", []),
                    "current_score": f.get("quality_score", 0)
                }
                for f in low_quality
            ]
        }

    def export_to_json(findings: list, filename: str) -> dict:
        """
        Export findings to a JSON file.

        Args:
            findings: List of findings to export
            filename: Name for the export file

        Returns:
            Export result with file path
        """
        import json
        from pathlib import Path
        from datetime import datetime

        export_dir = Path("./exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        filepath = export_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filepath, "w") as f:
            json.dump(findings, f, indent=2, default=str)

        return {
            "status": "success",
            "format": "json",
            "file_path": str(filepath),
            "records_exported": len(findings)
        }

    def export_to_csv(findings: list, filename: str) -> dict:
        """
        Export findings to a CSV file.

        Args:
            findings: List of findings to export
            filename: Name for the export file

        Returns:
            Export result with file path
        """
        import csv
        from pathlib import Path
        from datetime import datetime

        export_dir = Path("./exports")
        export_dir.mkdir(parents=True, exist_ok=True)

        filepath = export_dir / f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        if not findings:
            return {"status": "error", "message": "No findings to export"}

        # Get all unique keys
        all_keys = set()
        for f in findings:
            all_keys.update(f.keys())

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
            writer.writeheader()
            for finding in findings:
                # Convert complex objects to strings
                row = {k: str(v) if isinstance(v, (list, dict)) else v for k, v in finding.items()}
                writer.writerow(row)

        return {
            "status": "success",
            "format": "csv",
            "file_path": str(filepath),
            "records_exported": len(findings)
        }

    # Create the main agent with system instructions
    agent = Agent(
        model=settings.coordinator_model,
        name="chronicle",
        description="Marathon Research-to-Action Agent",
        instruction="""You are CHRONICLE, an autonomous research agent that transforms complex research goals into tangible deliverables.

## Your Capabilities
1. **Planning**: Break down research goals into actionable tasks
2. **Researching**: Search the web for relevant information using google_search
3. **Analyzing**: Synthesize findings into structured data
4. **Scoring**: Evaluate quality against criteria
5. **Self-Correcting**: Re-research when findings don't meet quality thresholds
6. **Exporting**: Create real file outputs (JSON, CSV)

## Research Process
1. First, understand the goal and create a research plan
2. Execute searches systematically
3. Analyze each result and extract structured data
4. Score findings against the criteria
5. If quality is below threshold, identify gaps and re-research
6. Once quality is met, export results

## Important Guidelines
- Be thorough and systematic
- Always verify information from multiple sources when possible
- Focus on the specific criteria provided
- Export results in the requested formats
- Report progress clearly

## Output Format
When you find relevant information, structure it as:
{
    "name": "Entity name",
    "description": "Brief description",
    "data": { ... relevant fields ... },
    "sources": ["url1", "url2"],
    "quality_score": 0.0-1.0
}
""",
        tools=[
            google_search,  # Built-in web search
            create_research_plan,
            analyze_finding,
            score_findings,
            export_to_json,
            export_to_csv
        ]
    )

    return agent


class ChronicleAgent:
    """
    Wrapper class for the CHRONICLE agent that provides
    high-level mission management.
    """

    def __init__(self):
        self.agent = create_chronicle_agent()
        self.client = client

    async def run_mission(
        self,
        goal: str,
        criteria: dict,
        actions_config: dict,
        on_progress: callable = None
    ) -> dict:
        """
        Run a complete research mission.

        Args:
            goal: The research goal
            criteria: Quality criteria
            actions_config: Export and notification config
            on_progress: Callback for progress updates

        Returns:
            Mission results with findings and exports
        """
        # Build the research prompt
        prompt = f"""
Research Goal: {goal}

Criteria:
- Required fields: {criteria.get('required_fields', ['name', 'description'])}
- Quality threshold: {criteria.get('quality_threshold', 0.8)}
- Target results: {criteria.get('max_results', 10)}
- Geographic focus: {criteria.get('geographic_focus', 'Global')}

Export formats requested: {actions_config.get('export_formats', ['json'])}

Please execute a comprehensive research mission:
1. Create a research plan
2. Search for relevant information
3. Analyze and score each finding
4. If quality is below threshold, re-research to fill gaps
5. Export results in the requested formats

Start by searching for relevant information about: {goal}
"""

        try:
            # Run the agent
            response = self.client.models.generate_content(
                model=self.agent.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    system_instruction=self.agent.instruction
                )
            )

            # Parse the response
            result = {
                "status": "completed",
                "response": response.text if hasattr(response, 'text') else str(response),
                "findings": [],
                "exports": []
            }

            return result

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "findings": [],
                "exports": []
            }

    async def search(self, query: str) -> list:
        """Execute a single search query."""
        try:
            response = self.client.models.generate_content(
                model=settings.researcher_model,
                contents=f"Search and summarize results for: {query}",
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return [{"query": query, "result": response.text if hasattr(response, 'text') else str(response)}]
        except Exception as e:
            return [{"query": query, "error": str(e)}]
