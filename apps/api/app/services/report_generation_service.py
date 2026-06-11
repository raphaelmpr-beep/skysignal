"""
ReportGenerationService — generates HTML and PDF threat assessment reports.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

TIER_COLORS = {
    "MINIMAL": "#22c55e",    # green
    "LOW": "#84cc16",        # lime
    "MODERATE": "#f59e0b",   # amber
    "ELEVATED": "#f97316",   # orange
    "HIGH": "#ef4444",       # red
}


class ReportGenerationService:
    def generate_html(
        self,
        assessment: Any,
        nearby_incidents: list[dict],
        org: Any,
    ) -> str:
        """
        Generate a complete HTML threat assessment report.

        Args:
            assessment:        FacilityAssessment ORM object
            nearby_incidents:  List of incident dicts (summary level)
            org:               Organization ORM object (may be None)

        Returns:
            Complete HTML string.
        """
        org_name = org.name if org else "SkySignal"
        tier = assessment.threat_tier or "UNKNOWN"
        tier_color = TIER_COLORS.get(tier, "#6b7280")
        score = assessment.threat_score or 0
        generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")

        # Factor breakdown rows
        factor_rows = _factor_rows(assessment)

        # Nearby incidents table rows
        incident_rows = _incident_rows(nearby_incidents)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SkySignal Facility Threat Assessment — {_esc(assessment.facility_name)}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1e293b; background: #fff; padding: 40px; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 3px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; }}
    .header-left h1 {{ font-size: 22px; font-weight: 700; color: #0f172a; }}
    .header-left .subtitle {{ font-size: 13px; color: #64748b; margin-top: 4px; }}
    .org-name {{ font-size: 14px; font-weight: 600; color: #334155; text-align: right; }}
    .generated {{ font-size: 11px; color: #94a3b8; text-align: right; margin-top: 4px; }}
    .section {{ margin-bottom: 32px; }}
    .section-title {{ font-size: 15px; font-weight: 700; color: #0f172a; border-left: 4px solid #3b82f6; padding-left: 10px; margin-bottom: 14px; text-transform: uppercase; letter-spacing: 0.05em; }}
    .score-block {{ display: inline-flex; align-items: center; gap: 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px 28px; }}
    .score-number {{ font-size: 56px; font-weight: 900; color: {tier_color}; line-height: 1; }}
    .score-meta {{ }}
    .score-tier {{ font-size: 22px; font-weight: 700; color: {tier_color}; }}
    .score-label {{ font-size: 12px; color: #94a3b8; margin-top: 2px; }}
    .facility-info {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px 20px; }}
    .facility-info table {{ width: 100%; border-collapse: collapse; }}
    .facility-info td {{ padding: 5px 8px; font-size: 14px; }}
    .facility-info td:first-child {{ font-weight: 600; color: #475569; width: 160px; }}
    table.data-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    table.data-table th {{ background: #0f172a; color: #fff; padding: 8px 12px; text-align: left; font-weight: 600; }}
    table.data-table td {{ padding: 8px 12px; border-bottom: 1px solid #e2e8f0; }}
    table.data-table tr:nth-child(even) td {{ background: #f8fafc; }}
    .bar-container {{ background: #e2e8f0; border-radius: 4px; height: 8px; width: 100px; display: inline-block; vertical-align: middle; }}
    .bar-fill {{ border-radius: 4px; height: 8px; display: inline-block; }}
    .disclaimer {{ background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 14px 18px; font-size: 12px; color: #78350f; }}
    .footer {{ margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center; }}
  </style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <h1>Facility Threat Assessment</h1>
    <div class="subtitle">SkySignal Drone Threat Intelligence Platform</div>
  </div>
  <div>
    <div class="org-name">{_esc(org_name)}</div>
    <div class="generated">Generated: {generated_at}</div>
  </div>
</div>

<!-- Threat Score -->
<div class="section">
  <div class="section-title">Threat Score</div>
  <div class="score-block">
    <div class="score-number">{score:.0f}</div>
    <div class="score-meta">
      <div class="score-tier" style="color:{tier_color}">{tier}</div>
      <div class="score-label">out of 100 &nbsp;|&nbsp; {assessment.incident_count} incident(s) analyzed</div>
    </div>
  </div>
</div>

<!-- Facility Info -->
<div class="section">
  <div class="section-title">Facility Details</div>
  <div class="facility-info">
    <table>
      <tr><td>Facility Name</td><td>{_esc(assessment.facility_name)}</td></tr>
      <tr><td>Address</td><td>{_esc(assessment.address or 'Not specified')}</td></tr>
      <tr><td>Coordinates</td><td>{assessment.lat:.6f}, {assessment.lon:.6f}</td></tr>
      <tr><td>Analysis Radius</td><td>{assessment.radius_miles} miles</td></tr>
      <tr><td>Time Window</td><td>{assessment.time_window_days} days</td></tr>
      <tr><td>Assessment Date</td><td>{assessment.created_at.strftime('%B %d, %Y') if assessment.created_at else 'N/A'}</td></tr>
    </table>
  </div>
</div>

<!-- Factor Breakdown -->
<div class="section">
  <div class="section-title">Factor Breakdown</div>
  <table class="data-table">
    <thead>
      <tr>
        <th>Factor</th>
        <th>Score (0–100)</th>
        <th>Weight</th>
        <th>Contribution</th>
      </tr>
    </thead>
    <tbody>
      {factor_rows}
    </tbody>
  </table>
</div>

<!-- Nearby Incidents -->
<div class="section">
  <div class="section-title">Nearby Incidents ({len(nearby_incidents)} shown)</div>
  {_incident_table(nearby_incidents) if nearby_incidents else '<p style="color:#94a3b8;font-size:13px;">No incident detail available.</p>'}
</div>

<!-- Explanation -->
<div class="section">
  <div class="section-title">Analysis Summary</div>
  <pre style="white-space:pre-wrap;font-family:inherit;font-size:13px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;color:#334155;">{_esc(assessment.explanation or 'No explanation available.')}</pre>
</div>

<!-- Disclaimer -->
<div class="section">
  <div class="disclaimer">
    <strong>Disclaimer:</strong> This report is generated from publicly available and user-submitted data sources.
    Threat scores are analytical estimates and do not constitute official threat assessments.
    SkySignal makes no warranties regarding completeness, accuracy, or fitness for any particular purpose.
    This report should be used as one input among many in security decision-making processes.
    Always consult qualified security professionals and official government sources.
  </div>
</div>

<div class="footer">
  SkySignal Drone Threat Intelligence Platform &nbsp;|&nbsp; Confidential — For Authorized Use Only
</div>

</body>
</html>"""
        return html

    def generate_pdf(self, html: str) -> bytes:
        """
        Convert HTML to PDF bytes.
        Tries WeasyPrint first; falls back to UTF-8 HTML bytes.

        Returns:
            PDF bytes (or HTML bytes if WeasyPrint unavailable).
        """
        try:
            from weasyprint import HTML as WeasyHTML
            return WeasyHTML(string=html).write_pdf()
        except ImportError:
            logger.warning(
                "WeasyPrint not installed. Returning HTML as bytes. "
                "Install with: pip install weasyprint"
            )
            return html.encode("utf-8")
        except Exception as exc:
            logger.error("WeasyPrint PDF generation failed: %s", exc)
            return html.encode("utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FACTOR_LABELS = {
    "evidence_confidence": ("Evidence Confidence", 0.30),
    "incident_density": ("Incident Density", 0.20),
    "recency": ("Recency", 0.15),
    "facility_proximity": ("Facility Proximity", 0.15),
    "severity": ("Severity", 0.10),
    "sector_sensitivity": ("Sector Sensitivity", 0.05),
    "repeat_pattern": ("Repeat Pattern", 0.05),
}

SCORE_ATTR_MAP = {
    "evidence_confidence": "evidence_confidence_score",
    "incident_density": "incident_density_score",
    "recency": "recency_score",
    "facility_proximity": "facility_proximity_score",
    "severity": "severity_score",
    "sector_sensitivity": "sector_sensitivity_score",
    "repeat_pattern": "repeat_pattern_score",
}


def _factor_rows(assessment) -> str:
    rows = []
    for key, (label, weight) in FACTOR_LABELS.items():
        attr = SCORE_ATTR_MAP[key]
        val = getattr(assessment, attr, None) or 0.0
        contribution = round(val * weight, 2)
        bar_width = int(val)
        color = _bar_color(val)
        rows.append(f"""
      <tr>
        <td>{label}</td>
        <td>
          <span style="font-weight:600;color:{color}">{val:.1f}</span>
          <span class="bar-container" style="margin-left:8px;">
            <span class="bar-fill" style="width:{bar_width}%;background:{color};"></span>
          </span>
        </td>
        <td>{int(weight * 100)}%</td>
        <td>{contribution:.2f}</td>
      </tr>""")
    return "".join(rows)


def _bar_color(val: float) -> str:
    if val >= 80:
        return "#ef4444"
    if val >= 60:
        return "#f97316"
    if val >= 40:
        return "#f59e0b"
    if val >= 20:
        return "#84cc16"
    return "#22c55e"


def _incident_rows(incidents: list[dict]) -> str:
    if not incidents:
        return ""
    rows = []
    for inc in incidents[:20]:  # cap at 20 rows
        rows.append(f"""
      <tr>
        <td>{_esc(str(inc.get('title', 'N/A')))}</td>
        <td>{_esc(str(inc.get('incident_type', 'N/A')))}</td>
        <td>{_esc(str(inc.get('severity', 'N/A')))}</td>
        <td>{_esc(str(inc.get('confidence_tier', 'N/A')))}</td>
        <td>{_esc(str(inc.get('occurred_at', 'N/A')))}</td>
      </tr>""")
    return "".join(rows)


def _incident_table(incidents: list[dict]) -> str:
    rows = _incident_rows(incidents)
    if not rows:
        return ""
    return f"""
  <table class="data-table">
    <thead>
      <tr>
        <th>Title</th>
        <th>Type</th>
        <th>Severity</th>
        <th>Confidence</th>
        <th>Occurred At</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>"""


def _esc(s: str) -> str:
    """Minimal HTML escaping."""
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
    )
