"""
CHRONICLE File Export Tools - Export deep research findings to various formats
"""
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import settings
from models.domain import Mission, DeepFinding


class FileExporter:
    """
    Export mission findings to various file formats.

    Supports: JSON, CSV, Markdown, PDF
    Optimized for rich DeepFinding data with pricing, features, pros/cons, etc.
    """

    def __init__(self, export_dir: Path = None):
        self.export_dir = export_dir or settings.export_dir
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _get_mission_dir(self, mission_id: str) -> Path:
        """Get export directory for a mission."""
        path = self.export_dir / mission_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _generate_filename(self, mission: Mission, format: str, prefix: str = None) -> str:
        """Generate a unique filename for export."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = prefix or f"chronicle_{mission.id}"
        return f"{base}_{timestamp}.{format}"

    def _normalize_finding(self, finding) -> Dict[str, Any]:
        """Convert finding to dictionary, handling both DeepFinding objects and dicts."""
        if isinstance(finding, DeepFinding):
            return finding.model_dump()
        elif isinstance(finding, dict):
            return finding
        elif isinstance(finding, list):
            # Handle list of items - convert to dict with names
            return {
                "name": ", ".join(str(f) for f in finding[:3]) if finding else "Unknown",
                "description": f"List of {len(finding)} items"
            }
        else:
            return {"name": str(finding), "description": ""}

    def _safe_get(self, obj, key, default=None):
        """Safely get a value from an object, handling non-dict types."""
        if isinstance(obj, dict):
            return obj.get(key, default)
        return default

    async def export(
        self,
        mission: Mission,
        format: str,
        include_metadata: bool = True,
        filename_prefix: str = None
    ) -> Dict[str, Any]:
        """
        Export mission findings to specified format.
        """
        format = format.lower()

        exporters = {
            "json": self._export_json,
            "csv": self._export_csv,
            "md": self._export_markdown,
            "markdown": self._export_markdown,
            "pdf": self._export_pdf
        }

        exporter = exporters.get(format)
        if not exporter:
            return {
                "status": "failed",
                "format": format,
                "error": f"Unsupported format: {format}"
            }

        try:
            result = await exporter(mission, include_metadata, filename_prefix)
            return result
        except Exception as e:
            return {
                "status": "failed",
                "format": format,
                "error": str(e)
            }

    async def _export_json(
        self,
        mission: Mission,
        include_metadata: bool,
        filename_prefix: str = None
    ) -> Dict[str, Any]:
        """Export to JSON format with full deep research data."""
        mission_dir = self._get_mission_dir(mission.id)
        filename = self._generate_filename(mission, "json", filename_prefix)
        filepath = mission_dir / filename

        # Normalize findings
        normalized_findings = [self._normalize_finding(f) for f in mission.findings]

        data = {
            "synthesis": mission.synthesis if mission.synthesis else {},
            "findings": normalized_findings,
            "research_stats": self._calculate_research_stats(normalized_findings)
        }

        if include_metadata:
            data["metadata"] = {
                "mission_id": mission.id,
                "goal": mission.goal,
                "criteria": mission.criteria,
                "total_findings": len(mission.findings),
                "deep_findings_count": sum(1 for f in normalized_findings if f.get("depth_score", 0) > 0.5),
                "has_synthesis": mission.synthesis is not None,
                "created_at": mission.created_at.isoformat(),
                "exported_at": datetime.utcnow().isoformat(),
                "research_depth": getattr(mission, 'depth', 'deep')
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return {
            "status": "success",
            "format": "json",
            "action_type": "export",
            "id": f"exp_{datetime.now().strftime('%H%M%S')}",
            "file_path": str(filepath),
            "file_url": f"/exports/{mission.id}/{filename}",
            "records_exported": len(mission.findings),
            "file_size_bytes": filepath.stat().st_size
        }

    def _calculate_research_stats(self, findings: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics about research depth."""
        if not findings:
            return {"total": 0}

        depth_scores = [f.get("depth_score", 0) for f in findings]
        attr_counts = [f.get("attribute_count", 0) for f in findings]
        source_counts = [f.get("source_count", 0) for f in findings]

        return {
            "total_findings": len(findings),
            "avg_depth_score": sum(depth_scores) / len(depth_scores) if depth_scores else 0,
            "avg_attributes": sum(attr_counts) / len(attr_counts) if attr_counts else 0,
            "avg_sources": sum(source_counts) / len(source_counts) if source_counts else 0,
            "high_quality_count": sum(1 for s in depth_scores if s >= 0.7),
            "with_pricing": sum(1 for f in findings if f.get("pricing")),
            "with_features": sum(1 for f in findings if f.get("features")),
            "with_pros_cons": sum(1 for f in findings if f.get("pros") or f.get("cons")),
        }

    async def _export_csv(
        self,
        mission: Mission,
        include_metadata: bool,
        filename_prefix: str = None
    ) -> Dict[str, Any]:
        """Export to CSV format optimized for DeepFinding data."""
        mission_dir = self._get_mission_dir(mission.id)
        filename = self._generate_filename(mission, "csv", filename_prefix)
        filepath = mission_dir / filename

        findings = [self._normalize_finding(f) for f in mission.findings]
        if not findings:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                f.write("No findings to export\n")
            return {
                "status": "success",
                "format": "csv",
                "action_type": "export",
                "id": f"exp_{datetime.now().strftime('%H%M%S')}",
                "file_path": str(filepath),
                "file_url": f"/exports/{mission.id}/{filename}",
                "records_exported": 0
            }

        # Define preferred column order for DeepFinding
        preferred_order = [
            "name", "category", "description", "depth_score", "attribute_count",
            "website", "pricing_summary", "features_summary", "pros_summary", "cons_summary",
            "use_cases_summary", "target_audience", "competitors_summary",
            "founded", "funding", "integrations_summary", "reviews_summary",
            "source_count", "sources_list"
        ]

        # Flatten complex fields for CSV
        csv_rows = []
        for finding in findings:
            row = {
                "name": finding.get("name", ""),
                "category": finding.get("category", ""),
                "description": finding.get("description", "")[:500],  # Truncate
                "depth_score": f"{finding.get('depth_score', 0):.2f}",
                "attribute_count": finding.get("attribute_count", 0),
                "website": finding.get("website", ""),
                "target_audience": finding.get("target_audience", ""),
                "founded": finding.get("founded", ""),
                "funding": finding.get("funding", ""),
                "reviews_summary": finding.get("reviews_summary", "")[:300],
                "source_count": finding.get("source_count", 0),
            }

            # Flatten pricing dict
            pricing = finding.get("pricing", {})
            if isinstance(pricing, dict):
                row["pricing_summary"] = self._format_pricing_summary(pricing)
            else:
                row["pricing_summary"] = str(pricing) if pricing else ""

            # Flatten lists
            row["features_summary"] = "; ".join(finding.get("features", [])[:5])
            row["pros_summary"] = "; ".join(finding.get("pros", [])[:3])
            row["cons_summary"] = "; ".join(finding.get("cons", [])[:3])
            row["use_cases_summary"] = "; ".join(finding.get("use_cases", [])[:3])
            row["competitors_summary"] = "; ".join(finding.get("competitors", [])[:5])
            row["integrations_summary"] = "; ".join(finding.get("integrations", [])[:5])
            row["sources_list"] = "; ".join(finding.get("sources", [])[:3])

            csv_rows.append(row)

        # Write CSV
        fieldnames = [col for col in preferred_order if any(row.get(col) for row in csv_rows)]

        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(csv_rows)

        return {
            "status": "success",
            "format": "csv",
            "action_type": "export",
            "id": f"exp_{datetime.now().strftime('%H%M%S')}",
            "file_path": str(filepath),
            "file_url": f"/exports/{mission.id}/{filename}",
            "records_exported": len(findings),
            "file_size_bytes": filepath.stat().st_size
        }

    def _format_pricing_summary(self, pricing) -> str:
        """Format pricing dict into readable summary."""
        if not pricing:
            return ""
        # Handle case where pricing is a list or string instead of dict
        if isinstance(pricing, list):
            return ", ".join(str(p) for p in pricing[:5])
        if isinstance(pricing, str):
            return pricing
        if not isinstance(pricing, dict):
            return str(pricing)
        parts = []
        if pricing.get("free_tier"):
            parts.append("Free tier available")
        if pricing.get("monthly"):
            parts.append(f"Monthly: {pricing['monthly']}")
        if pricing.get("annual"):
            parts.append(f"Annual: {pricing['annual']}")
        if pricing.get("enterprise"):
            parts.append(f"Enterprise: {pricing['enterprise']}")
        if pricing.get("tiers"):
            tiers = pricing["tiers"]
            if isinstance(tiers, list):
                parts.append(f"Tiers: {', '.join(str(t) for t in tiers[:3])}")
        return " | ".join(parts) if parts else json.dumps(pricing)

    async def _export_markdown(
        self,
        mission: Mission,
        include_metadata: bool,
        filename_prefix: str = None
    ) -> Dict[str, Any]:
        """Export to rich Markdown format showcasing deep research data."""
        mission_dir = self._get_mission_dir(mission.id)
        filename = self._generate_filename(mission, "md", filename_prefix)
        filepath = mission_dir / filename

        findings = [self._normalize_finding(f) for f in mission.findings]
        stats = self._calculate_research_stats(findings)

        lines = []

        # Header
        lines.append("# CHRONICLE Deep Research Report")
        lines.append("")
        lines.append(f"**Mission ID:** `{mission.id}`")
        lines.append(f"**Research Goal:** {mission.goal}")
        lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("")

        # Research Quality Summary
        lines.append("## Research Quality Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Entities Researched | {stats['total_findings']} |")
        lines.append(f"| Average Depth Score | {stats['avg_depth_score']:.2f} |")
        lines.append(f"| Average Attributes per Entity | {stats['avg_attributes']:.1f} |")
        lines.append(f"| High-Quality Findings (>0.7) | {stats['high_quality_count']} |")
        lines.append(f"| With Pricing Data | {stats['with_pricing']} |")
        lines.append(f"| With Feature Lists | {stats['with_features']} |")
        lines.append(f"| With Pros/Cons Analysis | {stats['with_pros_cons']} |")
        lines.append("")

        # Synthesis sections (if available)
        if mission.synthesis and isinstance(mission.synthesis, dict):
            syn = mission.synthesis
            lines.extend(self._render_synthesis_markdown(syn))

        # Quick Comparison Table (top findings)
        top_findings = sorted(findings, key=lambda f: f.get("depth_score", 0) if isinstance(f, dict) else 0, reverse=True)[:10]
        if top_findings:
            lines.append("## Quick Comparison: Top Findings")
            lines.append("")
            lines.append("| Name | Category | Depth Score | Has Pricing | Features | Pros | Cons |")
            lines.append("|------|----------|-------------|-------------|----------|------|------|")
            for f in top_findings:
                name = f.get("name", "Unknown")[:30]
                cat = f.get("category", "-")[:15]
                score = f"{f.get('depth_score', 0):.2f}"
                has_pricing = "Yes" if f.get("pricing") else "No"
                feat_count = len(f.get("features", []))
                pros_count = len(f.get("pros", []))
                cons_count = len(f.get("cons", []))
                lines.append(f"| {name} | {cat} | {score} | {has_pricing} | {feat_count} | {pros_count} | {cons_count} |")
            lines.append("")

        # Detailed Findings
        lines.append("---")
        lines.append("")
        lines.append("## Detailed Research Findings")
        lines.append("")

        for i, finding in enumerate(findings, 1):
            lines.extend(self._render_finding_markdown(i, finding))

        # Sources
        all_sources = []
        for f in findings:
            all_sources.extend(f.get("sources", []))
        if all_sources:
            lines.append("---")
            lines.append("")
            lines.append("## Sources & References")
            lines.append("")
            unique_sources = list(dict.fromkeys(all_sources))[:50]  # Dedupe, limit to 50
            for source in unique_sources:
                lines.append(f"- {source}")
            lines.append("")

        # Footer
        lines.append("")
        lines.append("---")
        lines.append("*Generated by CHRONICLE - Marathon Research-to-Action Agent*")
        lines.append(f"*Research completed with {sum(f.get('research_iterations', 0) for f in findings)} total queries*")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return {
            "status": "success",
            "format": "markdown",
            "action_type": "export",
            "id": f"exp_{datetime.now().strftime('%H%M%S')}",
            "file_path": str(filepath),
            "file_url": f"/exports/{mission.id}/{filename}",
            "records_exported": len(mission.findings),
            "file_size_bytes": filepath.stat().st_size
        }

    def _render_synthesis_markdown(self, syn: Dict) -> List[str]:
        """Render synthesis sections in markdown."""
        lines = []

        # Executive Summary
        if syn.get('executive_summary'):
            lines.append("## Executive Summary")
            lines.append("")
            lines.append(syn['executive_summary'])
            lines.append("")

        # Key Insights
        if syn.get('key_insights'):
            lines.append("## Key Insights")
            lines.append("")
            for insight in syn['key_insights']:
                lines.append(f"- {insight}")
            lines.append("")

        # Top Recommendations
        if syn.get('top_recommendations'):
            lines.append("## Top Recommendations")
            lines.append("")
            for rec in syn['top_recommendations']:
                # Handle case where rec might not be a dict
                if not isinstance(rec, dict):
                    lines.append(f"- {str(rec)[:200]}")
                    lines.append("")
                    continue
                rank = rec.get('rank', '')
                name = rec.get('name', 'Unknown')
                lines.append(f"### {rank}. {name}")
                lines.append("")
                if rec.get('reasoning'):
                    lines.append(f"**Why:** {rec['reasoning']}")
                    lines.append("")
                if rec.get('best_for'):
                    lines.append(f"**Best For:** {rec['best_for']}")
                    lines.append("")
                if rec.get('considerations'):
                    lines.append(f"**Considerations:** {rec['considerations']}")
                    lines.append("")

        # Comparison Matrix
        if syn.get('comparison_matrix'):
            matrix = syn['comparison_matrix']
            headers = matrix.get('headers', [])
            rows = matrix.get('rows', [])
            if headers and rows:
                lines.append("## Comparison Matrix")
                lines.append("")
                lines.append("| " + " | ".join(str(h) for h in headers) + " |")
                lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
                for row in rows:
                    lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
                lines.append("")

        # Market Analysis
        if syn.get('market_analysis'):
            lines.append("## Market Analysis")
            lines.append("")
            lines.append(syn['market_analysis'])
            lines.append("")

        # Next Steps
        if syn.get('next_steps'):
            lines.append("## Recommended Next Steps")
            lines.append("")
            for i, step in enumerate(syn['next_steps'], 1):
                lines.append(f"{i}. {step}")
            lines.append("")

        return lines

    def _render_finding_markdown(self, index: int, finding) -> List[str]:
        """Render a single DeepFinding in rich markdown format."""
        lines = []

        # Handle non-dict findings
        if not isinstance(finding, dict):
            lines.append(f"### {index}. {str(finding)[:100]}")
            lines.append("")
            return lines

        name = finding.get("name", "Unknown")
        category = finding.get("category", "")
        depth_score = finding.get("depth_score", 0)

        # Header with badge
        badge = "Deep" if depth_score >= 0.7 else "Moderate" if depth_score >= 0.4 else "Basic"
        lines.append(f"### {index}. {name}")
        if category:
            lines.append(f"**Category:** {category} | **Depth:** {badge} ({depth_score:.2f})")
        else:
            lines.append(f"**Depth:** {badge} ({depth_score:.2f})")
        lines.append("")

        # Description
        if finding.get("description"):
            lines.append(finding["description"])
            lines.append("")

        # Website & Basic Info
        info_parts = []
        if finding.get("website"):
            info_parts.append(f"[Website]({finding['website']})")
        if finding.get("founded"):
            info_parts.append(f"Founded: {finding['founded']}")
        if finding.get("funding"):
            info_parts.append(f"Funding: {finding['funding']}")
        if info_parts:
            lines.append(" | ".join(info_parts))
            lines.append("")

        # Pricing Table
        pricing = finding.get("pricing", {})
        if pricing and isinstance(pricing, dict):
            lines.append("#### Pricing")
            lines.append("")
            lines.append("| Tier | Price |")
            lines.append("|------|-------|")
            if pricing.get("free_tier"):
                lines.append("| Free | $0 |")
            if pricing.get("starter"):
                lines.append(f"| Starter | {pricing['starter']} |")
            if pricing.get("monthly"):
                lines.append(f"| Monthly | {pricing['monthly']} |")
            if pricing.get("pro") or pricing.get("professional"):
                lines.append(f"| Pro | {pricing.get('pro') or pricing.get('professional')} |")
            if pricing.get("annual"):
                lines.append(f"| Annual | {pricing['annual']} |")
            if pricing.get("enterprise"):
                lines.append(f"| Enterprise | {pricing['enterprise']} |")
            if pricing.get("tiers") and isinstance(pricing["tiers"], list):
                for tier in pricing["tiers"][:4]:
                    if isinstance(tier, dict):
                        lines.append(f"| {tier.get('name', 'Tier')} | {tier.get('price', 'N/A')} |")
                    else:
                        lines.append(f"| Tier | {tier} |")
            lines.append("")

        # Features
        features = finding.get("features", [])
        if features:
            lines.append("#### Key Features")
            lines.append("")
            for feat in features[:10]:  # Limit to 10
                lines.append(f"- {feat}")
            if len(features) > 10:
                lines.append(f"- *...and {len(features) - 10} more*")
            lines.append("")

        # Pros & Cons side by side
        pros = finding.get("pros", [])
        cons = finding.get("cons", [])
        if pros or cons:
            lines.append("#### Pros & Cons")
            lines.append("")
            lines.append("| Pros | Cons |")
            lines.append("|------|------|")
            max_rows = max(len(pros), len(cons), 1)
            for i in range(min(max_rows, 5)):  # Limit to 5 rows
                pro = f"+ {pros[i]}" if i < len(pros) else ""
                con = f"- {cons[i]}" if i < len(cons) else ""
                lines.append(f"| {pro} | {con} |")
            lines.append("")

        # Use Cases
        use_cases = finding.get("use_cases", [])
        if use_cases:
            lines.append("#### Best For")
            lines.append("")
            for uc in use_cases[:5]:
                lines.append(f"- {uc}")
            lines.append("")

        # Target Audience
        if finding.get("target_audience"):
            lines.append(f"**Target Audience:** {finding['target_audience']}")
            lines.append("")

        # Competitors
        competitors = finding.get("competitors", [])
        if competitors:
            lines.append(f"**Competitors:** {', '.join(competitors[:5])}")
            lines.append("")

        # Integrations
        integrations = finding.get("integrations", [])
        if integrations:
            lines.append(f"**Integrations:** {', '.join(integrations[:8])}")
            lines.append("")

        # Reviews Summary
        if finding.get("reviews_summary"):
            lines.append("#### User Reviews Summary")
            lines.append("")
            lines.append(f"*{finding['reviews_summary']}*")
            lines.append("")

        # Comparison Notes (if any)
        comparison_notes = finding.get("comparison_notes", {})
        if comparison_notes and isinstance(comparison_notes, dict):
            lines.append("#### Comparison Notes")
            lines.append("")
            for entity, note in list(comparison_notes.items())[:3]:
                lines.append(f"- **vs {entity}:** {note}")
            lines.append("")
        elif comparison_notes and isinstance(comparison_notes, list):
            lines.append("#### Comparison Notes")
            lines.append("")
            for note in comparison_notes[:3]:
                lines.append(f"- {note}")
            lines.append("")

        # Research metadata
        lines.append(f"*Research iterations: {finding.get('research_iterations', 0)} | Attributes: {finding.get('attribute_count', 0)} | Sources: {finding.get('source_count', 0)}*")
        lines.append("")
        lines.append("---")
        lines.append("")

        return lines

    async def _export_pdf(
        self,
        mission: Mission,
        include_metadata: bool,
        filename_prefix: str = None
    ) -> Dict[str, Any]:
        """Export to PDF format with rich DeepFinding data."""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        except ImportError:
            return {
                "status": "failed",
                "format": "pdf",
                "error": "reportlab not installed. Install with: pip install reportlab"
            }

        mission_dir = self._get_mission_dir(mission.id)
        filename = self._generate_filename(mission, "pdf", filename_prefix)
        filepath = mission_dir / filename

        findings = [self._normalize_finding(f) for f in mission.findings]
        stats = self._calculate_research_stats(findings)

        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#1a365d')
        )
        subtitle_style = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.grey
        )
        section_style = ParagraphStyle(
            'Section',
            parent=styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor('#2c5282')
        )

        story = []

        # Title Page
        story.append(Paragraph("CHRONICLE", title_style))
        story.append(Paragraph("Deep Research Report", subtitle_style))
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"<b>Research Goal:</b> {mission.goal}", styles['Normal']))
        story.append(Paragraph(f"<b>Mission ID:</b> {mission.id}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
        story.append(Spacer(1, 30))

        # Research Quality Summary
        story.append(Paragraph("Research Quality Metrics", section_style))
        quality_data = [
            ["Metric", "Value"],
            ["Total Entities Researched", str(stats['total_findings'])],
            ["Average Depth Score", f"{stats['avg_depth_score']:.2f}"],
            ["High-Quality Findings (>0.7)", str(stats['high_quality_count'])],
            ["With Pricing Data", str(stats['with_pricing'])],
            ["With Pros/Cons Analysis", str(stats['with_pros_cons'])],
        ]
        quality_table = Table(quality_data, colWidths=[3*inch, 2*inch])
        quality_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#e2e8f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ]))
        story.append(quality_table)
        story.append(Spacer(1, 20))

        # Synthesis sections
        if mission.synthesis and isinstance(mission.synthesis, dict):
            syn = mission.synthesis

            if syn.get('executive_summary'):
                story.append(Paragraph("Executive Summary", section_style))
                for para in syn['executive_summary'].split('\n\n')[:3]:
                    if para.strip():
                        story.append(Paragraph(para.strip()[:600], styles['Normal']))
                        story.append(Spacer(1, 8))
                story.append(Spacer(1, 12))

            if syn.get('key_insights'):
                story.append(Paragraph("Key Insights", section_style))
                for insight in syn['key_insights'][:8]:
                    story.append(Paragraph(f"• {insight}", styles['Normal']))
                story.append(Spacer(1, 12))

            if syn.get('top_recommendations'):
                story.append(Paragraph("Top Recommendations", section_style))
                for rec in syn['top_recommendations'][:5]:
                    # Handle case where rec might not be a dict
                    if not isinstance(rec, dict):
                        story.append(Paragraph(f"• {str(rec)[:200]}", styles['Normal']))
                        continue
                    rank = rec.get('rank', '')
                    name = rec.get('name', 'Unknown')
                    story.append(Paragraph(f"<b>{rank}. {name}</b>", styles['Heading3']))
                    if rec.get('reasoning'):
                        story.append(Paragraph(f"<i>{rec['reasoning'][:250]}</i>", styles['Normal']))
                    story.append(Spacer(1, 8))
                story.append(Spacer(1, 12))

        # Quick Comparison Table
        top_findings = sorted(findings, key=lambda f: f.get("depth_score", 0) if isinstance(f, dict) else 0, reverse=True)[:8]
        if top_findings:
            story.append(PageBreak())
            story.append(Paragraph("Quick Comparison: Top Findings", section_style))

            comp_data = [["Name", "Category", "Score", "Pricing", "Features"]]
            for f in top_findings:
                comp_data.append([
                    f.get("name", "Unknown")[:25],
                    f.get("category", "-")[:12],
                    f"{f.get('depth_score', 0):.2f}",
                    "Yes" if f.get("pricing") else "No",
                    str(len(f.get("features", [])))
                ])

            comp_table = Table(comp_data, colWidths=[2*inch, 1.2*inch, 0.7*inch, 0.8*inch, 0.8*inch])
            comp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ]))
            story.append(comp_table)
            story.append(Spacer(1, 20))

        # Detailed Findings
        story.append(Paragraph("Detailed Research Findings", section_style))
        story.append(Spacer(1, 10))

        for i, finding in enumerate(findings[:15], 1):  # Limit to 15 for PDF
            name = finding.get("name", "Unknown")
            category = finding.get("category", "")
            depth_score = finding.get("depth_score", 0)
            desc = finding.get("description", "No description")[:300]

            story.append(Paragraph(f"<b>{i}. {name}</b>", styles['Heading3']))
            if category:
                story.append(Paragraph(f"<i>Category: {category} | Depth Score: {depth_score:.2f}</i>", subtitle_style))
            story.append(Paragraph(desc, styles['Normal']))

            # Pricing summary
            pricing = finding.get("pricing", {})
            if pricing:
                pricing_text = self._format_pricing_summary(pricing)
                story.append(Paragraph(f"<b>Pricing:</b> {pricing_text}", styles['Normal']))

            # Features (brief)
            features = finding.get("features", [])
            if features:
                feat_text = ", ".join(features[:5])
                if len(features) > 5:
                    feat_text += f" (+{len(features)-5} more)"
                story.append(Paragraph(f"<b>Features:</b> {feat_text}", styles['Normal']))

            # Pros/Cons summary
            pros = finding.get("pros", [])
            cons = finding.get("cons", [])
            if pros:
                story.append(Paragraph(f"<b>Pros:</b> {'; '.join(pros[:3])}", styles['Normal']))
            if cons:
                story.append(Paragraph(f"<b>Cons:</b> {'; '.join(cons[:3])}", styles['Normal']))

            story.append(Spacer(1, 15))

        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph("---", styles['Normal']))
        story.append(Paragraph("<i>Generated by CHRONICLE - Marathon Research-to-Action Agent</i>", subtitle_style))

        # Build PDF
        doc.build(story)

        return {
            "status": "success",
            "format": "pdf",
            "action_type": "export",
            "id": f"exp_{datetime.now().strftime('%H%M%S')}",
            "file_path": str(filepath),
            "file_url": f"/exports/{mission.id}/{filename}",
            "records_exported": len(mission.findings),
            "file_size_bytes": filepath.stat().st_size
        }
