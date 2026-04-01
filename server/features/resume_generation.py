"""Resume generation — orchestrates three-step pipeline (generator → screener → refinement).

Coordinates independent pipeline stages and manages database persistence.
"""

from typing import Any

from db import job_descriptions, narratives, resume_variants
from pipeline.generator import _format_narratives, run_generator
from pipeline.refinement import _format_resume_for_screener, run_refinement
from pipeline.screener import run_screener


def _run_full_regenerate(jd_id: str, user_id: str, fit_report: dict[str, Any]) -> dict[str, Any]:
    """Full regenerate mode: all three steps from scratch.

    Uses pre-computed fit report to guide generator's strategic choices.
    """
    # Load inputs
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise ValueError(f"Job description not found: {jd_id}")

    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)

    # Step 1: Generate (guided by fit report)
    try:
        resume_data = run_generator(narratives_text, fit_report, user_id)
    except Exception as e:
        raise RuntimeError(f"generator_failed: {str(e)}")

    # Format resume for screener
    resume_text = _format_resume_for_screener(resume_data)

    # Step 2: Screen
    try:
        screener_data = run_screener(jd["content"], resume_text, user_id)
    except Exception as e:
        raise RuntimeError(f"screener_failed: {str(e)}")

    # Step 3: Refine
    try:
        refinement_data = run_refinement(
            resume_data, screener_data, narratives_text, jd["content"], user_id
        )
    except Exception as e:
        raise RuntimeError(f"refinement_failed: {str(e)}")

    # Build screener_report
    screener_report = {
        "screener_analysis": screener_data,
        "refinement_changes": {
            "sections_modified": [c["section"] for c in refinement_data.get("changes_made", [])],
            "changes": refinement_data.get("changes_made", []),
            "remaining_gaps": refinement_data.get("remaining_gaps", []),
            "coverage_improvement": refinement_data.get("coverage_improvement", 0),
        },
    }

    # Get version number
    latest = resume_variants.get_latest_variant(jd_id, user_id)
    version = (latest["version"] + 1) if latest else 1

    # Save to DB
    result = resume_variants.create_resume_variant(
        job_description_id=jd_id,
        user_id=user_id,
        content=refinement_data["refined_content"],
        version=version,
        screener_report=screener_report,
    )
    return result


def _run_refine_existing(
    jd_id: str, user_id: str, parent_variant_id: str, fit_report: dict[str, Any]
) -> dict[str, Any]:
    """Refine-existing mode: reuse generator + screener, run refinement only.

    Fit report is threaded through for consistency and future extensibility.
    """
    # Load inputs
    jd = job_descriptions.get_jd(jd_id, user_id)
    if jd is None:
        raise ValueError(f"Job description not found: {jd_id}")

    parent = resume_variants.get_latest_variant(jd_id, user_id)
    if parent is None or parent["id"] != parent_variant_id:
        raise ValueError(f"Variant not found: {parent_variant_id}")

    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)

    # Extract previous screener data from parent variant
    screener_report = parent.get("screener_report", {})
    screener_data = screener_report.get("screener_analysis", {})

    # Step 3: Refine (using previous screener data)
    try:
        refinement_data = run_refinement(
            {"summary": "", "experience": [], "skills": []},  # Placeholder, we use text version
            screener_data,
            narratives_text,
            jd["content"],
            user_id,
        )
    except Exception as e:
        raise RuntimeError(f"refinement_failed: {str(e)}")

    # Build updated screener_report
    updated_screener_report = {
        "screener_analysis": screener_data,
        "refinement_changes": {
            "sections_modified": [c["section"] for c in refinement_data.get("changes_made", [])],
            "changes": refinement_data.get("changes_made", []),
            "remaining_gaps": refinement_data.get("remaining_gaps", []),
            "coverage_improvement": refinement_data.get("coverage_improvement", 0),
        },
    }

    # Get version number
    version = parent["version"] + 1

    # Save new variant (refine-existing is a new version)
    result = resume_variants.create_resume_variant(
        job_description_id=jd_id,
        user_id=user_id,
        content=refinement_data["refined_content"],
        version=version,
        screener_report=updated_screener_report,
        parent_variant_id=parent_variant_id,
    )
    return result


def run_resume_generation(
    jd_id: str,
    user_id: str,
    fit_report: dict[str, Any],
    mode: str = "full",
    parent_variant_id: str | None = None,
) -> dict[str, Any]:
    """Run resume generation pipeline (generator → screener → refinement).

    Args:
        jd_id: Job description ID
        user_id: User ID
        fit_report: Pre-computed fit assessment (matches/gaps/terminology)
        mode: "full" for full regenerate, "refine" for refine-existing
        parent_variant_id: Variant to refine from (required if mode="refine")

    Returns:
        Resume variant row from database

    Raises:
        ValueError: If JD, variant, or fit_report not found
        RuntimeError: If any step fails
    """
    if mode == "full":
        return _run_full_regenerate(jd_id, user_id, fit_report)
    elif mode == "refine":
        if parent_variant_id is None:
            raise ValueError("parent_variant_id required for refine mode")
        return _run_refine_existing(jd_id, user_id, parent_variant_id, fit_report)
    else:
        raise ValueError(f"Unknown mode: {mode}")
