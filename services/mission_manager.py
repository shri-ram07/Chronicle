"""
CHRONICLE Mission Manager - Deep Research Orchestration

This module implements a multi-phase deep research system that produces
detailed, actionable findings instead of shallow lists of names.

Phases:
1. Planning - Create multi-query research strategy
2. Discovery - Find entities from multiple search angles
3. Deep Dive - Research each entity with 5+ targeted queries
4. Comparison - Compare top entities against each other
5. Validation - Verify key claims with additional sources
6. Semantic Scoring - LLM evaluates depth, not just field presence
7. Iterative Deepening - Re-research shallow findings
8. Synthesis - Generate comprehensive report
"""
import asyncio
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid

from google import genai
from google.genai import types

from config import settings
from models.domain import (
    Mission, MissionState, Checkpoint, ResearchPlan, ResearchTask,
    DeepFinding, ResearchPhase, ResearchDepth
)
from persistence import mission_store, checkpoint_store, event_bus


class MissionManager:
    """
    Manages deep research missions with multi-phase investigation.

    Key innovation: Instead of single LLM call per query producing shallow lists,
    we run 5+ queries per entity to gather rich attributes (pricing, features,
    pros/cons, use cases, etc.)
    """

    def __init__(self):
        # Default client using server's API key (may be None if not configured)
        self.default_client = None
        if settings.gemini_api_key:
            self.default_client = genai.Client(api_key=settings.gemini_api_key)
        self.client = self.default_client  # Current active client

    def _get_client(self, api_key: Optional[str] = None):
        """Get a Gemini client, using provided key or server default."""
        if api_key:
            return genai.Client(api_key=api_key)
        if self.default_client:
            return self.default_client
        raise ValueError("No API key provided and no server default configured. Please provide your Gemini API key.")

    # ===========================================
    # UTILITY METHODS
    # ===========================================

    def _sanitize_data(self, data: any) -> any:
        """Recursively sanitize data to ensure all types are JSON-serializable."""
        if data is None:
            return None
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, dict):
            return {str(k): self._sanitize_data(v) for k, v in data.items()}
        if isinstance(data, (list, tuple)):
            return [self._sanitize_data(item) for item in data]
        if isinstance(data, datetime):
            return data.isoformat()
        if isinstance(data, slice):
            return f"slice({data.start}, {data.stop}, {data.step})"
        return str(data)

    def _extract_text_from_response(self, response) -> str:
        """Safely extract text content from Gemini API response."""
        try:
            if hasattr(response, 'text'):
                text = response.text
                if isinstance(text, str):
                    return text
                return str(text)
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    if hasattr(candidate.content, 'parts') and candidate.content.parts:
                        parts_text = []
                        for part in candidate.content.parts:
                            if hasattr(part, 'text'):
                                parts_text.append(str(part.text))
                        return '\n'.join(parts_text)
            return str(response)
        except Exception as e:
            print(f"Error extracting text from response: {e}")
            return str(response)

    def _parse_json_from_text(self, text: str, default: any = None) -> any:
        """Extract and parse JSON from LLM response text."""
        try:
            # If default is a dict, prioritize finding object first
            if isinstance(default, dict):
                obj_match = re.search(r'\{[\s\S]*\}', text)
                if obj_match:
                    return json.loads(obj_match.group())
                array_match = re.search(r'\[[\s\S]*\]', text)
                if array_match:
                    return json.loads(array_match.group())
            else:
                # Try to find JSON array first
                array_match = re.search(r'\[[\s\S]*\]', text)
                if array_match:
                    return json.loads(array_match.group())
                # Try to find JSON object
                obj_match = re.search(r'\{[\s\S]*\}', text)
                if obj_match:
                    return json.loads(obj_match.group())
        except json.JSONDecodeError:
            pass
        return default if default is not None else {}

    async def _llm_query(self, prompt: str, use_search: bool = True) -> str:
        """Execute LLM query with optional Google Search grounding."""
        try:
            config = None
            if use_search and settings.enable_google_search:
                config = types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )

            response = self.client.models.generate_content(
                model=settings.researcher_model,
                contents=prompt,
                config=config
            )
            return self._extract_text_from_response(response)
        except Exception as e:
            print(f"LLM query error: {e}")
            return ""

    # ===========================================
    # MAIN MISSION EXECUTION
    # ===========================================

    async def run_mission(self, mission_id: str, api_key: Optional[str] = None) -> None:
        """
        Run a complete DEEP research mission.

        This is the main entry point. It orchestrates 8 phases of research
        to produce deeply researched findings instead of shallow name lists.

        Args:
            mission_id: The mission to run
            api_key: Optional user-provided Gemini API key
        """
        # Set the client for this mission run
        try:
            self.client = self._get_client(api_key)
        except ValueError as e:
            # No API key available - fail the mission
            mission = await mission_store.get(mission_id)
            if mission:
                mission.state = MissionState.FAILED
                mission.error_message = str(e)
                await mission_store.save(mission)
                await event_bus.emit_error(mission_id, {"error": str(e)})
            return

        mission = await mission_store.get(mission_id)
        if not mission:
            print(f"Mission {mission_id} not found")
            return

        # Determine research depth from request
        depth = mission.settings.get("depth", settings.research_depth)
        target_count = mission.criteria.get("max_results", settings.target_entities)

        try:
            start_time = datetime.utcnow()

            # ============ PHASE 1: PLANNING ============
            await self._update_mission(mission, MissionState.PLANNING,
                                       "Creating deep research plan...")
            plan = await self._create_deep_plan(mission)
            mission.plan = plan
            mission.total_steps = 8  # 8 phases
            await mission_store.save(mission)

            # ============ PHASE 2: DISCOVERY ============
            await self._update_mission(mission, MissionState.RESEARCHING,
                                       "Phase 1/4: Discovering entities...")
            entities = await self._execute_discovery_phase(mission)
            mission.completed_steps = 1
            await mission_store.save(mission)

            # ============ PHASE 3: DEEP DIVE ============
            await self._update_mission(mission, MissionState.RESEARCHING,
                                       "Phase 2/4: Deep diving into entities...")
            deep_findings = await self._execute_deep_dive_phase(mission, entities)
            mission.completed_steps = 2
            await mission_store.save(mission)

            # ============ PHASE 4: COMPARISON ============
            await self._update_mission(mission, MissionState.ANALYZING,
                                       "Phase 3/4: Comparing entities...")
            compared_findings = await self._execute_comparison_phase(mission, deep_findings)
            mission.completed_steps = 3
            await mission_store.save(mission)

            # ============ PHASE 5: VALIDATION ============
            await self._update_mission(mission, MissionState.ANALYZING,
                                       "Phase 4/4: Validating claims...")
            validated_findings = await self._execute_validation_phase(mission, compared_findings)
            mission.completed_steps = 4
            await mission_store.save(mission)

            # ============ PHASE 6: SEMANTIC SCORING ============
            await self._update_mission(mission, MissionState.SCORING,
                                       "Evaluating research depth...")
            score_result = await self._semantic_quality_score(mission, validated_findings)
            mission.completed_steps = 5
            await mission_store.save(mission)

            # ============ PHASE 7: ITERATIVE DEEPENING ============
            iterations = 0
            while (score_result.get("needs_more_depth", False) and
                   iterations < settings.max_deepening_iterations):
                await self._update_mission(mission, MissionState.CORRECTING,
                                          f"Deepening shallow findings (iteration {iterations + 1})...")
                validated_findings = await self._iterative_deepen(
                    mission, validated_findings, score_result
                )
                score_result = await self._semantic_quality_score(mission, validated_findings)
                iterations += 1
                mission.corrections_made = iterations

            mission.completed_steps = 6
            await mission_store.save(mission)

            # Convert DeepFindings to dicts and save
            for finding in validated_findings:
                finding_dict = finding.to_dict() if hasattr(finding, 'to_dict') else self._sanitize_data(finding.__dict__)
                mission.add_finding(finding_dict)
                await event_bus.emit_finding(mission_id, finding_dict)

            await mission_store.save(mission)

            # ============ PHASE 8: SYNTHESIS ============
            await self._update_mission(mission, MissionState.ANALYZING,
                                       "Synthesizing comprehensive report...")
            synthesis = await self._synthesize_deep_report(mission, validated_findings, score_result)
            mission.synthesis = synthesis
            mission.completed_steps = 7
            await mission_store.save(mission)

            # ============ EXPORT ============
            await self._update_mission(mission, MissionState.EXPORTING,
                                       "Creating exports...")
            exports = await self._export_results(mission)

            for export in exports:
                mission.add_action(export)
                await event_bus.emit_action(mission_id, export)

            # ============ COMPLETE ============
            mission.completed_at = datetime.utcnow()
            mission.completed_steps = 8
            duration = (mission.completed_at - start_time).total_seconds()

            await self._update_mission(mission, MissionState.COMPLETED,
                                       f"Deep research completed in {duration/60:.1f} minutes!")

            await event_bus.emit_complete(mission_id, {
                "findings_count": len(mission.findings),
                "exports_count": len(exports),
                "corrections_made": mission.corrections_made,
                "duration_seconds": duration,
                "average_depth_score": score_result.get("overall_score", 0)
            })

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Mission {mission_id} failed: {e}")
            print(f"Full traceback:\n{error_trace}")
            try:
                with open(f"error_{mission_id}.log", "w") as f:
                    f.write(f"Error: {e}\n\nTraceback:\n{error_trace}")
            except:
                pass
            await self._update_mission(mission, MissionState.FAILED, f"Error: {str(e)}")
            await event_bus.emit_error(mission_id, str(e))

    async def _update_mission(self, mission: Mission, state: MissionState, activity: str) -> None:
        """Update mission state and emit event."""
        mission.update_state(state, activity)
        await mission_store.save(mission)
        await event_bus.emit_status(mission.id, state.value, activity)

    # ===========================================
    # PHASE 1: DEEP PLANNING
    # ===========================================

    async def _create_deep_plan(self, mission: Mission) -> ResearchPlan:
        """Create a multi-phase deep research plan with multiple query angles."""
        prompt = f"""Create a comprehensive deep research plan for:

GOAL: {mission.goal}

Generate a strategic plan with MULTIPLE search queries for each phase.
Think about different angles to find and deeply research entities.

Return a JSON object:
{{
    "strategy": "Overall research approach (2-3 sentences)",
    "discovery_queries": [
        "direct search for {mission.goal}",
        "best/top rated version of the goal",
        "alternatives and competitors",
        "recommended for specific use cases",
        "industry leaders in this space"
    ],
    "deep_dive_aspects": [
        "pricing and plans",
        "features and capabilities",
        "pros and cons from reviews",
        "use cases and target audience",
        "integrations and technical details"
    ],
    "estimated_duration_minutes": 30
}}

Return ONLY the JSON object."""

        text = await self._llm_query(prompt, use_search=False)
        plan_data = self._parse_json_from_text(text, {
            "strategy": "Systematic deep research",
            "discovery_queries": [mission.goal],
            "deep_dive_aspects": ["pricing", "features", "reviews"],
            "estimated_duration_minutes": 30
        })

        # Convert to ResearchPlan
        discovery_queries = plan_data.get("discovery_queries", [mission.goal])
        tasks = [ResearchTask(query=q) for q in discovery_queries]

        return ResearchPlan(
            goal=mission.goal,
            strategy=plan_data.get("strategy", "Deep research"),
            tasks=tasks,
            estimated_duration_minutes=plan_data.get("estimated_duration_minutes", 30)
        )

    # ===========================================
    # PHASE 2: DISCOVERY
    # ===========================================

    async def _execute_discovery_phase(self, mission: Mission) -> List[Dict]:
        """
        Discover entities using multiple search queries from different angles.
        Returns basic entity info (name, category, description).
        """
        discovered = []
        seen_names = set()

        # Generate discovery queries
        queries = [
            f"best {mission.goal} 2024 2025",
            f"top rated {mission.goal}",
            f"{mission.goal} alternatives comparison",
            f"recommended {mission.goal} for business",
            f"{mission.goal} market leaders popular"
        ]

        # Add plan queries if available
        if mission.plan and mission.plan.tasks:
            for task in mission.plan.tasks[:3]:
                if task.query not in queries:
                    queries.append(task.query)

        total_queries = min(len(queries), settings.discovery_queries)

        for i, query in enumerate(queries[:total_queries]):
            await event_bus.emit_progress(
                mission.id, i + 1, total_queries,
                f"Discovery: {query[:40]}..."
            )

            prompt = f"""Search for: {query}

Find entities/products/services that match this query.
For each one found, provide:
- name: Official name
- category: Type/category
- brief_description: 1-2 sentence description
- website: URL if known

Return as JSON array. Find 5-10 relevant entities.
Example: [{{"name": "Example", "category": "Software", "brief_description": "A tool for...", "website": "example.com"}}]"""

            text = await self._llm_query(prompt, use_search=True)
            entities = self._parse_json_from_text(text, [])

            if isinstance(entities, list):
                for entity in entities:
                    if isinstance(entity, dict):
                        name = entity.get("name", "").strip()
                        name_lower = name.lower()
                        if name and name_lower not in seen_names:
                            seen_names.add(name_lower)
                            entity["discovered_via"] = query
                            discovered.append(entity)

            await asyncio.sleep(settings.delay_between_queries_seconds)

        # Limit to target count
        target = mission.criteria.get("max_results", settings.target_entities)
        return discovered[:target]

    # ===========================================
    # PHASE 3: DEEP DIVE (THE KEY INNOVATION)
    # ===========================================

    async def _execute_deep_dive_phase(
        self, mission: Mission, entities: List[Dict]
    ) -> List[DeepFinding]:
        """
        Deep dive into each entity with multiple targeted queries.
        This is THE KEY PHASE that transforms shallow names into rich data.

        For each entity, we run 5 queries to get:
        - Pricing details
        - Features list
        - Pros and cons
        - Use cases
        - Technical details
        """
        deep_findings = []
        total = len(entities)

        for i, entity in enumerate(entities):
            entity_name = entity.get("name", "Unknown")
            await event_bus.emit_progress(
                mission.id, i + 1, total,
                f"Deep diving: {entity_name}"
            )

            # Create DeepFinding from discovered entity
            finding = DeepFinding(
                name=entity_name,
                category=entity.get("category", ""),
                description=entity.get("brief_description", ""),
                website=entity.get("website")
            )

            # Query 1: PRICING
            pricing_text = await self._llm_query(
                f"Find detailed pricing information for {entity_name}. "
                f"Include all pricing tiers, monthly/annual costs, free trial info. "
                f"Return JSON: {{\"tiers\": [...], \"starting_price\": \"...\", \"free_trial\": true/false}}"
            )
            pricing_data = self._parse_json_from_text(pricing_text)
            if pricing_data:
                finding.pricing = self._sanitize_data(pricing_data)
            finding.research_queries.append(f"{entity_name} pricing")
            await asyncio.sleep(settings.delay_between_queries_seconds)

            # Query 2: FEATURES
            features_text = await self._llm_query(
                f"List the main features and capabilities of {entity_name}. "
                f"Be specific - what can users actually do with it? "
                f"Return JSON array of feature strings: [\"feature1\", \"feature2\", ...]"
            )
            features = self._parse_json_from_text(features_text, [])
            if isinstance(features, list):
                finding.features = [str(f) for f in features[:15]]
            finding.research_queries.append(f"{entity_name} features")
            await asyncio.sleep(settings.delay_between_queries_seconds)

            # Query 3: PROS AND CONS
            proscons_text = await self._llm_query(
                f"What are the pros and cons of {entity_name} based on user reviews? "
                f"Be specific with real advantages and disadvantages. "
                f"Return JSON: {{\"pros\": [...], \"cons\": [...]}}"
            )
            proscons = self._parse_json_from_text(proscons_text, {})
            if isinstance(proscons, dict):
                finding.pros = [str(p) for p in proscons.get("pros", [])[:8]]
                finding.cons = [str(c) for c in proscons.get("cons", [])[:8]]
            finding.research_queries.append(f"{entity_name} reviews pros cons")
            await asyncio.sleep(settings.delay_between_queries_seconds)

            # Query 4: USE CASES & TARGET AUDIENCE
            usecases_text = await self._llm_query(
                f"Who should use {entity_name}? What are the best use cases? "
                f"Return JSON: {{\"use_cases\": [...], \"target_audience\": \"...\", \"best_for\": \"...\"}}"
            )
            usecases = self._parse_json_from_text(usecases_text, {})
            if isinstance(usecases, dict):
                finding.use_cases = [str(u) for u in usecases.get("use_cases", [])[:8]]
                finding.target_audience = str(usecases.get("target_audience", ""))
            finding.research_queries.append(f"{entity_name} use cases")
            await asyncio.sleep(settings.delay_between_queries_seconds)

            # Query 5: COMPETITORS & INTEGRATIONS
            compare_text = await self._llm_query(
                f"What are the main competitors to {entity_name}? What integrations does it support? "
                f"Return JSON: {{\"competitors\": [...], \"integrations\": [...]}}"
            )
            compare = self._parse_json_from_text(compare_text, {})
            if isinstance(compare, dict):
                finding.competitors = [str(c) for c in compare.get("competitors", [])[:8]]
                finding.integrations = [str(i) for i in compare.get("integrations", [])[:10]]
            finding.research_queries.append(f"{entity_name} competitors integrations")

            # Calculate attribute count and initial depth score
            finding.research_iterations = 5
            finding.attribute_count = self._count_attributes(finding)
            finding.depth_score = self._calculate_depth_score(finding)
            finding.last_deepened = datetime.utcnow()

            deep_findings.append(finding)

        return deep_findings

    def _count_attributes(self, finding: DeepFinding) -> int:
        """Count how many attributes have been populated."""
        count = 0
        if finding.pricing:
            count += 1
        if finding.features:
            count += 1
        if finding.pros:
            count += 1
        if finding.cons:
            count += 1
        if finding.use_cases:
            count += 1
        if finding.target_audience:
            count += 1
        if finding.competitors:
            count += 1
        if finding.integrations:
            count += 1
        if finding.website:
            count += 1
        if finding.description:
            count += 1
        return count

    def _calculate_depth_score(self, finding: DeepFinding) -> float:
        """Calculate depth score based on attribute richness."""
        max_score = 10  # 10 key attributes
        score = self._count_attributes(finding)

        # Bonus for rich data
        if finding.features and len(finding.features) >= 5:
            score += 0.5
        if finding.pros and len(finding.pros) >= 3:
            score += 0.5
        if finding.cons and len(finding.cons) >= 3:
            score += 0.5
        if finding.pricing and isinstance(finding.pricing, dict) and finding.pricing.get("tiers"):
            score += 0.5

        return min(score / max_score, 1.0)

    # ===========================================
    # PHASE 4: COMPARISON
    # ===========================================

    async def _execute_comparison_phase(
        self, mission: Mission, findings: List[DeepFinding]
    ) -> List[DeepFinding]:
        """Compare top entities against each other."""
        if len(findings) < 2:
            return findings

        # Sort by depth score and compare top entities
        sorted_findings = sorted(findings, key=lambda f: f.depth_score, reverse=True)
        top_count = min(len(sorted_findings), 8)
        top_findings = sorted_findings[:top_count]

        pairs_done = 0
        max_pairs = min(settings.comparison_pairs, 10)

        for i, finding_a in enumerate(top_findings):
            for finding_b in top_findings[i+1:i+3]:  # Compare with next 2
                if pairs_done >= max_pairs:
                    break

                await event_bus.emit_progress(
                    mission.id, pairs_done + 1, max_pairs,
                    f"Comparing: {finding_a.name} vs {finding_b.name}"
                )

                compare_text = await self._llm_query(
                    f"Compare {finding_a.name} vs {finding_b.name}. "
                    f"Which is better for different use cases? "
                    f"Return JSON: {{\"winner_overall\": \"...\", \"comparison\": \"2-3 sentence comparison\"}}"
                )
                compare_data = self._parse_json_from_text(compare_text, {})

                if isinstance(compare_data, dict):
                    comparison_note = compare_data.get("comparison", "")
                    finding_a.comparison_notes[finding_b.name] = comparison_note
                    finding_b.comparison_notes[finding_a.name] = comparison_note

                pairs_done += 1
                await asyncio.sleep(settings.delay_between_queries_seconds)

            if pairs_done >= max_pairs:
                break

        return findings

    # ===========================================
    # PHASE 5: VALIDATION
    # ===========================================

    async def _execute_validation_phase(
        self, mission: Mission, findings: List[DeepFinding]
    ) -> List[DeepFinding]:
        """Validate key claims for top findings."""
        # Only validate top findings
        sorted_findings = sorted(findings, key=lambda f: f.depth_score, reverse=True)
        to_validate = sorted_findings[:min(len(sorted_findings), 10)]

        for i, finding in enumerate(to_validate):
            await event_bus.emit_progress(
                mission.id, i + 1, len(to_validate),
                f"Validating: {finding.name}"
            )

            # Validate pricing if present
            if finding.pricing:
                validation_text = await self._llm_query(
                    f"Verify the pricing information for {finding.name}. "
                    f"Find official pricing from their website. "
                    f"Return JSON: {{\"verified\": true/false, \"current_pricing\": \"...\", \"source\": \"...\"}}"
                )
                validation = self._parse_json_from_text(validation_text, {})
                if validation.get("source"):
                    finding.sources.append(str(validation.get("source")))

            finding.source_count = len(finding.sources)
            await asyncio.sleep(settings.delay_between_queries_seconds)

        return findings

    # ===========================================
    # PHASE 6: SEMANTIC QUALITY SCORING
    # ===========================================

    async def _semantic_quality_score(
        self, mission: Mission, findings: List[DeepFinding]
    ) -> Dict:
        """Use LLM to evaluate content depth, not just field presence."""
        # Prepare summary for evaluation
        summary = []
        for f in findings[:15]:
            summary.append({
                "name": f.name,
                "has_pricing": f.pricing is not None,
                "features_count": len(f.features),
                "pros_count": len(f.pros),
                "cons_count": len(f.cons),
                "use_cases_count": len(f.use_cases),
                "depth_score": f.depth_score
            })

        prompt = f"""Evaluate the depth and quality of this research:

GOAL: {mission.goal}
FINDINGS COUNT: {len(findings)}
SAMPLE: {json.dumps(summary, indent=2)}

Evaluate on:
1. SPECIFICITY - Are details specific (actual prices, named features) or vague?
2. COMPLETENESS - Do findings have pricing, features, pros, cons, use cases?
3. ACTIONABILITY - Could someone make a decision from this data?

Return JSON:
{{
    "overall_score": 0.0-1.0,
    "needs_more_depth": true/false,
    "shallow_findings": ["name1", "name2"],
    "missing_attributes": ["pricing", "features"],
    "recommendations": ["Get more specific pricing", "Add more use cases"]
}}"""

        text = await self._llm_query(prompt, use_search=False)
        result = self._parse_json_from_text(text, {
            "overall_score": 0.7,
            "needs_more_depth": False,
            "shallow_findings": [],
            "missing_attributes": [],
            "recommendations": []
        })

        # Calculate aggregate score
        avg_depth = sum(f.depth_score for f in findings) / len(findings) if findings else 0
        result["average_depth_score"] = avg_depth

        return result

    # ===========================================
    # PHASE 7: ITERATIVE DEEPENING
    # ===========================================

    async def _iterative_deepen(
        self, mission: Mission, findings: List[DeepFinding], score_result: Dict
    ) -> List[DeepFinding]:
        """Re-research shallow findings with targeted queries."""
        shallow_names = set(score_result.get("shallow_findings", []))
        missing_attrs = score_result.get("missing_attributes", [])

        for finding in findings:
            if finding.name in shallow_names or finding.depth_score < settings.depth_score_threshold:
                await event_bus.emit_progress(
                    mission.id, 0, 1,
                    f"Deepening: {finding.name}"
                )

                # Target missing attributes
                for attr in missing_attrs[:3]:
                    if attr == "pricing" and not finding.pricing:
                        text = await self._llm_query(
                            f"Find SPECIFIC pricing for {finding.name}. "
                            f"Include exact prices, tiers, and what's included."
                        )
                        data = self._parse_json_from_text(text)
                        if data:
                            finding.pricing = self._sanitize_data(data)

                    elif attr == "features" and len(finding.features) < 5:
                        text = await self._llm_query(
                            f"List SPECIFIC features of {finding.name}. "
                            f"Not generic descriptions - actual capabilities."
                        )
                        features = self._parse_json_from_text(text, [])
                        if features:
                            finding.features.extend([str(f) for f in features[:10]])

                    await asyncio.sleep(settings.delay_between_queries_seconds)

                # Recalculate scores
                finding.research_iterations += 1
                finding.attribute_count = self._count_attributes(finding)
                finding.depth_score = self._calculate_depth_score(finding)
                finding.last_deepened = datetime.utcnow()

        return findings

    # ===========================================
    # PHASE 8: SYNTHESIS
    # ===========================================

    async def _synthesize_deep_report(
        self, mission: Mission, findings: List[DeepFinding], score_result: Dict
    ) -> Dict:
        """Generate comprehensive synthesis report from deep findings."""
        # Prepare findings data
        findings_data = []
        for f in findings[:30]:
            findings_data.append({
                "name": f.name,
                "category": f.category,
                "description": f.description,
                "pricing": f.pricing,
                "features": f.features[:10],
                "pros": f.pros[:5],
                "cons": f.cons[:5],
                "use_cases": f.use_cases[:5],
                "target_audience": f.target_audience,
                "competitors": f.competitors[:5],
                "depth_score": f.depth_score
            })

        prompt = f"""Create a comprehensive research report based on deep analysis.

RESEARCH GOAL: {mission.goal}
QUALITY METRICS:
- Total findings: {len(findings)}
- Average depth score: {score_result.get('average_depth_score', 0):.2f}

FINDINGS DATA:
{json.dumps(findings_data, indent=2, default=str)}

Generate a detailed JSON report:
{{
    "executive_summary": "3-4 paragraph comprehensive summary with specific names, prices, and recommendations...",
    "key_insights": ["Insight 1 with specific data...", "Insight 2...", ...],
    "top_recommendations": [
        {{
            "rank": 1,
            "name": "Top pick name",
            "reasoning": "Why this is #1 with specific evidence...",
            "best_for": "Ideal use case",
            "pricing_summary": "Price overview"
        }}
    ],
    "comparison_matrix": {{
        "headers": ["Name", "Pricing", "Best For", "Key Strength"],
        "rows": [["Entity1", "$X/mo", "Teams", "Feature"], ...]
    }},
    "market_analysis": "2-3 paragraphs on market trends based on the findings...",
    "strengths_weaknesses": [
        {{
            "name": "Entity name",
            "strengths": ["Strength 1", "Strength 2"],
            "weaknesses": ["Weakness 1"],
            "verdict": "Overall assessment"
        }}
    ],
    "next_steps": ["Actionable step 1...", "Step 2...", ...],
    "methodology": "Description of research methodology used"
}}

Be SPECIFIC - use actual names, prices, and data from the findings."""

        text = await self._llm_query(prompt, use_search=False)
        synthesis = self._parse_json_from_text(text, self._generate_fallback_synthesis(mission, findings, score_result))

        # Ensure synthesis is a dict (fallback if LLM returned a list)
        if not isinstance(synthesis, dict):
            synthesis = self._generate_fallback_synthesis(mission, findings, score_result)

        synthesis["generated_at"] = datetime.utcnow().isoformat()
        synthesis["total_findings_analyzed"] = len(findings)
        synthesis["average_depth_score"] = score_result.get("average_depth_score", 0)

        return self._sanitize_data(synthesis)

    def _generate_fallback_synthesis(
        self, mission: Mission, findings: List[DeepFinding], score_result: Dict
    ) -> Dict:
        """Generate basic synthesis if LLM fails."""
        top_items = sorted(findings, key=lambda f: f.depth_score, reverse=True)[:10]

        return {
            "executive_summary": f"Deep research completed for: {mission.goal}. "
                                 f"Analyzed {len(findings)} entities with an average depth score of "
                                 f"{score_result.get('average_depth_score', 0):.2f}.",
            "key_insights": [
                f"Found {len(findings)} deeply researched entities",
                f"Top recommendation: {top_items[0].name if top_items else 'N/A'}",
                f"Average research depth: {score_result.get('average_depth_score', 0):.2f}"
            ],
            "top_recommendations": [
                {
                    "rank": i + 1,
                    "name": f.name,
                    "reasoning": f.description[:200] if f.description else "See detailed findings",
                    "best_for": f.use_cases[0] if f.use_cases else "General use"
                }
                for i, f in enumerate(top_items[:5])
            ],
            "comparison_matrix": {
                "headers": ["Name", "Category", "Depth Score"],
                "rows": [[f.name, f.category, f"{f.depth_score:.2f}"] for f in top_items[:10]]
            },
            "market_analysis": "See individual findings for detailed market analysis.",
            "strengths_weaknesses": [
                {
                    "name": f.name,
                    "strengths": f.pros[:3],
                    "weaknesses": f.cons[:3],
                    "verdict": "Review detailed findings"
                }
                for f in top_items[:5]
            ],
            "next_steps": [
                "Review top recommendations in detail",
                "Compare shortlisted options",
                "Conduct trials with top picks"
            ],
            "methodology": f"Deep research using {sum(f.research_iterations for f in findings)} targeted queries "
                          f"across {len(findings)} entities."
        }

    # ===========================================
    # EXPORT
    # ===========================================

    async def _export_results(self, mission: Mission) -> List[Dict]:
        """Export mission results to configured formats."""
        from tools.file_export import FileExporter

        exporter = FileExporter()
        exports = []

        formats = mission.actions_config.get("export_formats", ["json", "md"])

        for format in formats:
            try:
                result = await exporter.export(
                    mission=mission,
                    format=format,
                    include_metadata=True
                )
                exports.append(result)
            except Exception as e:
                exports.append({
                    "format": format,
                    "status": "failed",
                    "error": str(e)
                })

        return exports

    # ===========================================
    # RESUME SUPPORT
    # ===========================================

    async def resume_mission(self, mission_id: str, checkpoint: Checkpoint) -> None:
        """Resume a mission from a checkpoint."""
        mission = await mission_store.get(mission_id)
        if not mission:
            return

        mission.findings = checkpoint.findings
        mission.completed_steps = checkpoint.current_task_index
        mission.thought_signature = checkpoint.thought_signature

        await self.run_mission(mission_id)
