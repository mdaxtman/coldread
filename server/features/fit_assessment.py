"""Fit assessment — Strong / Moderate / Borderline / Poor with gap detection.

Orchestrates fit assessment pipeline stage and manages database persistence.
"""

from typing import Any

from db import fit_reports, job_descriptions, narratives
from pipeline.fit_assessment import run_fit_assessment
from pipeline.generator import _format_narratives
from security.injection_detection import analyze_jd_for_injection


def run_fit_assessment_workflow(jd_id: str, user_id: str) -> Any:
    """Run fit assessment pipeline and save results.

    Args:
        jd_id: Job description ID
        user_id: Current user ID

    Returns:
        Fit report record from database

    Raises:
        ValueError: If JD not found
        RuntimeError: If assessment fails
    """
    # Load inputs
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise ValueError(f"Job description not found: {jd_id}")

    # Analyze for suspicious patterns (non-blocking, for monitoring)
    analyze_jd_for_injection(jd["content"], user_id)

    # Load and format narratives
    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)

    # Run fit assessment
    try:
        result = run_fit_assessment(jd["content"], narratives_text, user_id)
    except Exception as e:
        raise RuntimeError(f"fit_assessment_failed: {str(e)}")

    # Save to DB
    return fit_reports.create_fit_report(
        job_description_id=jd_id,
        user_id=user_id,
        fit_level=result["fit_level"],
        matches=result["matches"],
        gaps=result["gaps"],
        terminology=result["terminology"],
        reasoning=result["reasoning"],
    )
