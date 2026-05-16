"""Resume generation — orchestrates three-step pipeline (fit assessment → generation → refinement).

Coordinates independent pipeline stages and manages database persistence.
"""

from typing import Any

from db import job_descriptions, narratives, resume_variants
from pipeline.fit_assessment_stage import run_fit_assessment_stage
from pipeline.generator import _format_narratives, run_generator
from pipeline.refinement import _format_resume_for_screener, run_refinement
from pipeline.refinement_stage import run_refinement_stage
from pipeline.resume_generation_stage import run_resume_generation_stage
from pipeline.screener import run_screener
from pipeline.stage_input import (
    FitAssessmentInput,
    RefinementInput,
    ResumeGenerationInput,
)

# ============================================================================
# New Orchestration Layer: Calling Independent Pipeline Stages
# ============================================================================


def _fit_output_to_dict(fit_output) -> dict[str, Any]:
    """Convert FitAssessmentOutput to dict for database storage.

    Args:
        fit_output: FitAssessmentOutput dataclass instance

    Returns:
        Dictionary representation suitable for database storage
    """
    return {
        "fit_level": fit_output.fit_level,
        "matches": fit_output.matches,
        "gaps": fit_output.gaps,
        "terminology": fit_output.terminology,
        "overall_score": fit_output.overall_score,
        "semantic_score": fit_output.semantic_score,
        "keyword_coverage": fit_output.keyword_coverage,
    }


def run_full_pipeline(
    jd_content: str,
    narratives_text: str,
    contact_info: dict[str, str] | None,
    user_id: str,
    refine: bool = True,
) -> dict[str, Any]:
    """Orchestrate the full resume generation pipeline.

    Coordinates three independent pipeline stages in sequence:
    Stage 1: Fit Assessment (ATS perspective) — evaluate candidate against JD
    Stage 2: Resume Generation (writer perspective) — create tailored resume
    Stage 3: Refinement (editor perspective, optional) — improve and align

    Args:
        jd_content: Raw job description text
        narratives_text: Formatted candidate background narratives
        contact_info: Optional contact information (email, phone, location, etc.)
        user_id: Current user ID (scoped for multi-user readiness)
        refine: Whether to run the refinement stage (default True)

    Returns:
        Dictionary with keys:
        - fit_report: Full fit assessment output as dict
        - resume_content: Final resume markdown string
        - contact_info: Contact info dict or None

    Raises:
        RuntimeError: If any stage fails
        ValueError: If prompts not found
    """
    # Stage 1: Fit Assessment (ATS screener perspective)
    try:
        fit_input = FitAssessmentInput(
            jd_content=jd_content,
            narratives_text=narratives_text,
            user_id=user_id,
        )
        fit_output = run_fit_assessment_stage(fit_input)
    except Exception as e:
        raise RuntimeError(f"fit_assessment_failed: {str(e)}")

    # Stage 2: Resume Generation (writer perspective)
    try:
        gen_input = ResumeGenerationInput(
            narratives_text=narratives_text,
            fit_assessment_output=fit_output,
            contact_info=contact_info,
            user_id=user_id,
        )
        gen_output = run_resume_generation_stage(gen_input)
    except Exception as e:
        raise RuntimeError(f"resume_generation_failed: {str(e)}")

    # Stage 3: Refinement (editor perspective, optional)
    if refine:
        try:
            refine_input = RefinementInput(
                resume_content=gen_output.content,
                fit_assessment_output=fit_output,
                jd_content=jd_content,
                user_id=user_id,
            )
            refine_output = run_refinement_stage(refine_input)
            final_content = refine_output.refined_content
        except Exception as e:
            raise RuntimeError(f"refinement_failed: {str(e)}")
    else:
        final_content = gen_output.content

    # Convert fit_output to dict for storage
    fit_report = _fit_output_to_dict(fit_output)

    return {
        "fit_report": fit_report,
        "resume_content": final_content,
        "contact_info": gen_output.contact_info,
    }


# ============================================================================
# Legacy Orchestration Functions (for backward compatibility)
# ============================================================================


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

    # Extract contact info from career overview narrative
    overview = next((n for n in narrative_rows if n.get("category") == "career_overview"), None)
    contact_info = overview.get("contact_info") if overview else None

    # Step 1: Generate (guided by fit report)
    try:
        resume_data = run_generator(narratives_text, fit_report, contact_info, user_id)
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
            resume_data, dict(screener_data), narratives_text, jd["content"], user_id
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
        contact_info=contact_info,
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

    parent = resume_variants.get_variant_by_id(parent_variant_id, user_id)
    if parent is None:
        raise ValueError(f"Variant not found: {parent_variant_id}")

    narrative_rows = narratives.list_narratives(user_id)
    narratives_text = _format_narratives(narrative_rows)

    # Extract contact info from career overview narrative
    overview = next((n for n in narrative_rows if n.get("category") == "career_overview"), None)
    contact_info = overview.get("contact_info") if overview else None

    # Extract previous screener data from parent variant
    screener_report = parent.get("screener_report", {})
    screener_data = screener_report.get("screener_analysis", {})

    # Step 3: Refine (using previous screener data)
    try:
        refinement_data = run_refinement(
            {},  # Resume data not used in refine mode; uses screener_report instead
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
        contact_info=contact_info,
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
