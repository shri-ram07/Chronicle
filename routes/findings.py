"""
CHRONICLE Findings Routes - Access research findings
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from models import Finding
from persistence import mission_store

router = APIRouter()


@router.get("/findings/{mission_id}")
async def get_findings(
    mission_id: str,
    min_score: Optional[float] = None,
    verified_only: bool = False,
    limit: int = 100,
    offset: int = 0
):
    """
    Get all findings for a mission.

    Supports filtering by quality score and verification status.
    """
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    findings = mission.findings

    # Apply filters
    if min_score is not None:
        findings = [f for f in findings if f.get("quality_score", 0) >= min_score]

    if verified_only:
        findings = [f for f in findings if f.get("verified", False)]

    # Apply pagination
    total = len(findings)
    findings = findings[offset:offset + limit]

    return {
        "mission_id": mission_id,
        "findings": findings,
        "total": total,
        "filtered": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/findings/{mission_id}/{finding_id}")
async def get_finding(mission_id: str, finding_id: str):
    """Get a specific finding by ID."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    finding = next(
        (f for f in mission.findings if f.get("id") == finding_id),
        None
    )

    if not finding:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

    return finding


@router.get("/findings/{mission_id}/summary")
async def get_findings_summary(mission_id: str):
    """Get a summary of findings for a mission."""
    mission = await mission_store.get(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    findings = mission.findings
    if not findings:
        return {
            "mission_id": mission_id,
            "total_findings": 0,
            "average_quality": 0.0,
            "verified_count": 0,
            "by_source": {}
        }

    # Calculate statistics
    quality_scores = [f.get("quality_score", 0) for f in findings]
    verified_count = sum(1 for f in findings if f.get("verified", False))

    # Group by sources
    source_counts = {}
    for f in findings:
        for source in f.get("sources", ["unknown"]):
            source_counts[source] = source_counts.get(source, 0) + 1

    return {
        "mission_id": mission_id,
        "total_findings": len(findings),
        "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
        "min_quality": min(quality_scores) if quality_scores else 0.0,
        "max_quality": max(quality_scores) if quality_scores else 0.0,
        "verified_count": verified_count,
        "verification_rate": verified_count / len(findings) if findings else 0.0,
        "by_source": source_counts
    }
