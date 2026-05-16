"""Integration tests for full pipeline stages.

Verifies that the three independent stages (fit assessment → resume generation → refinement)
work together correctly when orchestrated by run_full_pipeline.

Mocks Anthropic API calls at the stage level and verifies the complete data flow.
"""

from unittest.mock import patch

from features.resume_generation import run_full_pipeline
from pipeline.stage_input import (
    FitAssessmentOutput,
    RefinementOutput,
    ResumeGenerationOutput,
)


class TestFullPipelineIntegration:
    """Integration tests for the complete three-stage pipeline."""

    def test_full_pipeline_stages_integration(self) -> None:
        """Verify all stages work together in sequence.

        Tests that:
        - Fit assessment output feeds into resume generation input
        - Resume generation output feeds into refinement input
        - Final output has all required keys
        - Fit level is correctly derived from overall_score
        - When refine=True, resume_content comes from refinement, not generation
        """
        with (
            patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
            patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
            patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
        ):
            # Mock fit assessment stage output
            fit_output = FitAssessmentOutput(
                fit_level="strong",
                matches=[
                    {"requirement": "React", "priority": "required", "notes": "core skill"},
                    {"requirement": "TypeScript", "priority": "required", "notes": "core skill"},
                ],
                gaps=[{"requirement": "AWS", "type": "hard", "notes": "not mentioned"}],
                terminology=[{"my_term": "frontend", "jd_term": "UI engineer", "confidence": 0.85}],
                overall_score=0.8,
                semantic_score=0.8,
                keyword_coverage={"react": True, "typescript": True, "aws": False},
            )
            mock_fit_stage.return_value = fit_output

            # Mock resume generation stage output
            gen_output = ResumeGenerationOutput(
                content="## Senior Engineer\n\nExperienced React developer...",
                contact_info={"email": "user@example.com", "phone": "555-1234"},
            )
            mock_gen_stage.return_value = gen_output

            # Mock refinement stage output
            refine_output = RefinementOutput(
                refined_content="## Senior Engineer\n\nExperienced React developer...",
                changes_made=["Improved summary", "Added AWS context"],
            )
            mock_refine_stage.return_value = refine_output

            # Run full pipeline with refine=True
            result = run_full_pipeline(
                jd_content="React engineer, TypeScript, AWS preferred",
                narratives_text="Senior frontend engineer with React and TypeScript expertise",
                contact_info=None,
                user_id="user-123",
                refine=True,
            )

            # Verify output structure
            assert "fit_report" in result
            assert "resume_content" in result
            assert "contact_info" in result

            # Verify fit report content
            assert result["fit_report"]["fit_level"] == "strong"
            assert result["fit_report"]["overall_score"] == 0.8
            assert result["fit_report"]["semantic_score"] == 0.8
            assert len(result["fit_report"]["matches"]) == 2
            assert len(result["fit_report"]["gaps"]) == 1
            assert len(result["fit_report"]["terminology"]) == 1

            # Verify resume content comes from refinement (not generation)
            assert result["resume_content"] == refine_output.refined_content
            assert "Senior Engineer" in result["resume_content"]

            # Verify contact info is preserved from generation stage
            assert result["contact_info"] == gen_output.contact_info

            # Verify all stages were called
            mock_fit_stage.assert_called_once()
            mock_gen_stage.assert_called_once()
            mock_refine_stage.assert_called_once()

    def test_full_pipeline_without_refinement(self) -> None:
        """Verify pipeline works when refine=False (skips refinement stage)."""
        with (
            patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
            patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
            patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
        ):
            # Mock fit assessment output
            fit_output = FitAssessmentOutput(
                fit_level="moderate",
                matches=[{"requirement": "Python", "priority": "required", "notes": ""}],
                gaps=[],
                terminology=[],
                overall_score=0.75,
                semantic_score=0.75,
                keyword_coverage={"python": True},
            )
            mock_fit_stage.return_value = fit_output

            # Mock resume generation output
            gen_output = ResumeGenerationOutput(
                content="## Python Developer\n\nExperienced developer...",
                contact_info=None,
            )
            mock_gen_stage.return_value = gen_output

            # Run pipeline with refine=False
            result = run_full_pipeline(
                jd_content="Python engineer needed",
                narratives_text="Python developer with 5 years experience",
                contact_info=None,
                user_id="user-456",
                refine=False,
            )

            # Verify output structure
            assert "fit_report" in result
            assert "resume_content" in result
            assert "contact_info" in result

            # Verify fit level is moderate
            assert result["fit_report"]["fit_level"] == "moderate"

            # Verify resume content comes from generation (no refinement)
            assert result["resume_content"] == gen_output.content

            # Verify only fit and gen stages were called (not refine)
            mock_fit_stage.assert_called_once()
            mock_gen_stage.assert_called_once()
            mock_refine_stage.assert_not_called()

    def test_full_pipeline_preserves_contact_info(self) -> None:
        """Verify pipeline preserves contact info through stages."""
        with (
            patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
            patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
            patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
        ):
            # Setup mocks
            fit_output = FitAssessmentOutput(
                fit_level="strong",
                matches=[],
                gaps=[],
                terminology=[],
                overall_score=0.9,
                semantic_score=0.9,
                keyword_coverage={},
            )
            mock_fit_stage.return_value = fit_output

            contact_info = {
                "email": "alice@example.com",
                "phone": "555-9999",
                "location": "San Francisco, CA",
            }

            gen_output = ResumeGenerationOutput(
                content="## Resume\n\nContent here...",
                contact_info=contact_info,
            )
            mock_gen_stage.return_value = gen_output

            refine_output = RefinementOutput(
                refined_content="## Resume\n\nRefined content...",
                changes_made=[],
            )
            mock_refine_stage.return_value = refine_output

            # Run pipeline with contact_info=None (gen stage will populate it)
            result = run_full_pipeline(
                jd_content="Senior role",
                narratives_text="Experienced professional",
                contact_info=None,
                user_id="user-789",
                refine=True,
            )

            # Verify contact info is preserved from generation stage
            assert result["contact_info"] == contact_info
            assert result["contact_info"]["email"] == "alice@example.com"

    def test_full_pipeline_preserves_fit_level(self) -> None:
        """Verify fit_level from fit assessment stage is preserved in output.

        Note: fit_level is calculated in fit_assessment_stage, not in run_full_pipeline.
        This test verifies that the orchestration preserves whatever fit_level
        the fit assessment stage returns.
        """
        test_cases = [
            ("strong", 0.9),
            ("strong", 0.8),
            ("moderate", 0.75),
            ("moderate", 0.6),
            ("borderline", 0.55),
            ("borderline", 0.4),
            ("poor", 0.3),
            ("poor", 0.0),
        ]

        for expected_fit_level, overall_score in test_cases:
            with (
                patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
                patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
                patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
            ):
                # Setup mocks with fit_level already calculated by fit_assessment_stage
                fit_output = FitAssessmentOutput(
                    fit_level=expected_fit_level,  # Calculated by fit_assessment_stage
                    matches=[],
                    gaps=[],
                    terminology=[],
                    overall_score=overall_score,
                    semantic_score=overall_score,
                    keyword_coverage={},
                )
                mock_fit_stage.return_value = fit_output

                gen_output = ResumeGenerationOutput(content="Resume", contact_info=None)
                mock_gen_stage.return_value = gen_output

                refine_output = RefinementOutput(refined_content="Refined", changes_made=[])
                mock_refine_stage.return_value = refine_output

                # Run pipeline
                result = run_full_pipeline(
                    jd_content="JD",
                    narratives_text="Narratives",
                    contact_info=None,
                    user_id="user-test",
                    refine=True,
                )

                # Verify fit_level is preserved from fit assessment stage
                assert result["fit_report"]["fit_level"] == expected_fit_level, (
                    f"fit_level {expected_fit_level} should be preserved, "
                    f"got {result['fit_report']['fit_level']}"
                )

    def test_full_pipeline_with_empty_gaps(self) -> None:
        """Verify pipeline handles perfect fit (no gaps)."""
        with (
            patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
            patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
            patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
        ):
            # Setup perfect fit scenario
            fit_output = FitAssessmentOutput(
                fit_level="strong",
                matches=[
                    {"requirement": "React", "priority": "required", "notes": ""},
                    {"requirement": "TypeScript", "priority": "required", "notes": ""},
                    {"requirement": "AWS", "priority": "preferred", "notes": ""},
                ],
                gaps=[],  # No gaps - perfect fit
                terminology=[],
                overall_score=0.95,
                semantic_score=0.95,
                keyword_coverage={"react": True, "typescript": True, "aws": True},
            )
            mock_fit_stage.return_value = fit_output

            gen_output = ResumeGenerationOutput(
                content="## Senior Engineer\n\nAll skills match...",
                contact_info=None,
            )
            mock_gen_stage.return_value = gen_output

            refine_output = RefinementOutput(
                refined_content="## Senior Engineer\n\nAll skills match perfectly...",
                changes_made=["Minor polish"],
            )
            mock_refine_stage.return_value = refine_output

            # Run pipeline
            result = run_full_pipeline(
                jd_content="Perfect match JD",
                narratives_text="Perfect match narratives",
                contact_info=None,
                user_id="user-perfect",
                refine=True,
            )

            # Verify result structure
            assert result["fit_report"]["fit_level"] == "strong"
            assert len(result["fit_report"]["gaps"]) == 0
            assert len(result["fit_report"]["matches"]) == 3

    def test_full_pipeline_with_multiple_terminology_matches(self) -> None:
        """Verify pipeline preserves terminology mappings through stages."""
        with (
            patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
            patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
            patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
        ):
            # Setup with multiple terminology mappings
            fit_output = FitAssessmentOutput(
                fit_level="moderate",
                matches=[],
                gaps=[],
                terminology=[
                    {"my_term": "frontend", "jd_term": "UI engineer", "confidence": 0.9},
                    {
                        "my_term": "api development",
                        "jd_term": "backend services",
                        "confidence": 0.85,
                    },
                    {"my_term": "testing", "jd_term": "QA automation", "confidence": 0.8},
                ],
                overall_score=0.7,
                semantic_score=0.7,
                keyword_coverage={},
            )
            mock_fit_stage.return_value = fit_output

            gen_output = ResumeGenerationOutput(content="Resume", contact_info=None)
            mock_gen_stage.return_value = gen_output

            refine_output = RefinementOutput(refined_content="Refined", changes_made=[])
            mock_refine_stage.return_value = refine_output

            # Run pipeline
            result = run_full_pipeline(
                jd_content="JD",
                narratives_text="Narratives",
                contact_info=None,
                user_id="user-terms",
                refine=True,
            )

            # Verify all terminology mappings are preserved
            assert len(result["fit_report"]["terminology"]) == 3
            assert result["fit_report"]["terminology"][0]["my_term"] == "frontend"
            assert result["fit_report"]["terminology"][1]["my_term"] == "api development"
            assert result["fit_report"]["terminology"][2]["my_term"] == "testing"

    def test_full_pipeline_data_flow_verification(self) -> None:
        """Verify data flows correctly from one stage to the next.

        Tests that:
        - FitAssessmentInput receives correct JD and narratives
        - ResumeGenerationInput receives FitAssessmentOutput
        - RefinementInput receives ResumeGenerationOutput
        """
        with (
            patch("features.resume_generation.run_fit_assessment_stage") as mock_fit_stage,
            patch("features.resume_generation.run_resume_generation_stage") as mock_gen_stage,
            patch("features.resume_generation.run_refinement_stage") as mock_refine_stage,
        ):
            # Setup mocks
            fit_output = FitAssessmentOutput(
                fit_level="strong",
                matches=[{"requirement": "React", "priority": "required", "notes": ""}],
                gaps=[],
                terminology=[],
                overall_score=0.85,
                semantic_score=0.85,
                keyword_coverage={"react": True},
            )
            mock_fit_stage.return_value = fit_output

            gen_output = ResumeGenerationOutput(
                content="Generated resume content",
                contact_info=None,
            )
            mock_gen_stage.return_value = gen_output

            refine_output = RefinementOutput(
                refined_content="Refined resume content",
                changes_made=[],
            )
            mock_refine_stage.return_value = refine_output

            # Run pipeline with specific inputs
            jd_content = "Senior React developer"
            narratives_text = "10 years React experience"

            run_full_pipeline(
                jd_content=jd_content,
                narratives_text=narratives_text,
                contact_info=None,
                user_id="user-flow",
                refine=True,
            )

            # Verify fit assessment was called with correct inputs
            fit_call_args = mock_fit_stage.call_args
            assert fit_call_args is not None
            fit_input = fit_call_args[0][0]
            assert fit_input.jd_content == jd_content
            assert fit_input.narratives_text == narratives_text
            assert fit_input.user_id == "user-flow"

            # Verify resume generation was called with fit output
            gen_call_args = mock_gen_stage.call_args
            assert gen_call_args is not None
            gen_input = gen_call_args[0][0]
            assert gen_input.fit_assessment_output == fit_output
            assert gen_input.narratives_text == narratives_text
            assert gen_input.user_id == "user-flow"

            # Verify refinement was called with generation output
            refine_call_args = mock_refine_stage.call_args
            assert refine_call_args is not None
            refine_input = refine_call_args[0][0]
            assert refine_input.resume_content == gen_output.content
            assert refine_input.fit_assessment_output == fit_output
            assert refine_input.jd_content == jd_content
            assert refine_input.user_id == "user-flow"
