"""Tests for pipeline stage input/output contracts.

Validates that dataclass definitions correctly enforce required fields,
support optional fields, and maintain type safety across stage boundaries.
"""

import pytest

from pipeline.stage_input import (
    FitAssessmentInput,
    FitAssessmentOutput,
    RefinementInput,
    RefinementOutput,
    ResumeGenerationInput,
    ResumeGenerationOutput,
)


class TestFitAssessmentInput:
    """Validate FitAssessmentInput contract."""

    def test_valid_input_creation(self) -> None:
        """Should accept valid input with all required fields."""
        input_data = FitAssessmentInput(
            jd_content="React engineer, 5+ years",
            narratives_text="Senior frontend engineer...",
            user_id="user-123",
        )
        assert input_data.jd_content == "React engineer, 5+ years"
        assert input_data.narratives_text == "Senior frontend engineer..."
        assert input_data.user_id == "user-123"

    def test_missing_required_field_jd_content(self) -> None:
        """Should reject missing jd_content."""
        with pytest.raises(TypeError):
            FitAssessmentInput(  # type: ignore[call-arg]
                narratives_text="text",
                user_id="user-123",
            )

    def test_missing_required_field_narratives_text(self) -> None:
        """Should reject missing narratives_text."""
        with pytest.raises(TypeError):
            FitAssessmentInput(  # type: ignore[call-arg]
                jd_content="text",
                user_id="user-123",
            )

    def test_missing_required_field_user_id(self) -> None:
        """Should reject missing user_id."""
        with pytest.raises(TypeError):
            FitAssessmentInput(  # type: ignore[call-arg]
                jd_content="text",
                narratives_text="text",
            )


class TestFitAssessmentOutput:
    """Validate FitAssessmentOutput contract."""

    def test_valid_output_creation(self) -> None:
        """Should accept valid output with all required fields."""
        output = FitAssessmentOutput(
            fit_level="strong",
            matches=[{"requirement": "Python", "priority": "required", "notes": "primary"}],
            gaps=[],
            terminology=[],
            overall_score=0.85,
            semantic_score=0.88,
            keyword_coverage={"Python": True, "React": True, "AWS": False},
        )
        assert output.fit_level == "strong"
        assert len(output.matches) == 1
        assert output.matches[0]["requirement"] == "Python"
        assert len(output.gaps) == 0
        assert len(output.terminology) == 0
        assert output.overall_score == 0.85
        assert output.semantic_score == 0.88
        assert output.keyword_coverage["Python"] is True

    def test_fit_level_with_enum_values(self) -> None:
        """Should support all valid fit level values."""
        for level in ["strong", "moderate", "borderline", "poor"]:
            output = FitAssessmentOutput(
                fit_level=level,
                matches=[],
                gaps=[],
                terminology=[],
                overall_score=0.5,
                semantic_score=0.5,
                keyword_coverage={},
            )
            assert output.fit_level == level

    def test_matches_with_multiple_entries(self) -> None:
        """Should support multiple matches with nested dict structure."""
        matches = [
            {"requirement": "Python", "priority": "required", "notes": "core skill"},
            {"requirement": "React", "priority": "preferred", "notes": "bonus"},
        ]
        output = FitAssessmentOutput(
            fit_level="strong",
            matches=matches,
            gaps=[],
            terminology=[],
            overall_score=0.9,
            semantic_score=0.92,
            keyword_coverage={"Python": True, "React": True},
        )
        assert len(output.matches) == 2

    def test_gaps_with_hard_and_soft_types(self) -> None:
        """Should support both hard and soft gap types."""
        gaps = [
            {"requirement": "10+ years", "type": "hard", "notes": "experience requirement"},
            {"requirement": "AWS", "type": "soft", "notes": "nice to have"},
        ]
        output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[],
            gaps=gaps,
            terminology=[],
            overall_score=0.65,
            semantic_score=0.68,
            keyword_coverage={"AWS": False},
        )
        assert len(output.gaps) == 2
        assert output.gaps[0]["type"] == "hard"
        assert output.gaps[1]["type"] == "soft"

    def test_terminology_mappings(self) -> None:
        """Should support terminology mappings with confidence scores."""
        terminology: list[dict[str, str | float]] = [
            {"my_term": "React", "jd_term": "React.js", "confidence": 0.95},
            {"my_term": "REST API", "jd_term": "RESTful API", "confidence": 0.85},
        ]
        output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=terminology,
            overall_score=0.88,
            semantic_score=0.90,
            keyword_coverage={"React": True, "REST": True},
        )
        assert len(output.terminology) == 2


class TestResumeGenerationInput:
    """Validate ResumeGenerationInput contract."""

    def test_valid_input_with_all_fields(self) -> None:
        """Should accept valid input with fit assessment and contact info."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.85,
            semantic_score=0.88,
            keyword_coverage={},
        )
        input_data = ResumeGenerationInput(
            narratives_text="Background text",
            fit_assessment_output=fit_output,
            contact_info={
                "email": "test@example.com",
                "phone": "555-1234",
                "location": "San Francisco",
            },
            user_id="user-123",
        )
        assert input_data.narratives_text == "Background text"
        assert input_data.fit_assessment_output.fit_level == "strong"
        assert input_data.contact_info is not None
        assert input_data.contact_info["email"] == "test@example.com"
        assert input_data.user_id == "user-123"

    def test_valid_input_without_contact_info(self) -> None:
        """Should accept valid input with contact_info as None."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.85,
            semantic_score=0.88,
            keyword_coverage={},
        )
        input_data = ResumeGenerationInput(
            narratives_text="Background text",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )
        assert input_data.contact_info is None

    def test_fit_assessment_output_nesting(self) -> None:
        """Should properly nest FitAssessmentOutput as a field."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[{"requirement": "Python", "priority": "required", "notes": ""}],
            gaps=[{"requirement": "10+ years", "type": "hard", "notes": ""}],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.68,
            keyword_coverage={"Python": True},
        )
        input_data = ResumeGenerationInput(
            narratives_text="Text",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )
        assert input_data.fit_assessment_output.fit_level == "moderate"
        assert len(input_data.fit_assessment_output.matches) == 1


class TestResumeGenerationOutput:
    """Validate ResumeGenerationOutput contract."""

    def test_valid_output_creation(self) -> None:
        """Should accept valid resume generation output."""
        resume_content = """# Resume

## Summary
Experienced engineer with 8+ years in full-stack development

## Experience
### Senior Engineer at TechCorp (2020-2024)
- Built and shipped core platform features
- Led team of 3 engineers
"""
        output = ResumeGenerationOutput(
            content=resume_content,
            contact_info={"email": "test@example.com", "linkedin": "linkedin.com/in/test"},
        )
        assert "Resume" in output.content
        assert "Senior Engineer" in output.content
        assert output.contact_info is not None
        assert output.contact_info["email"] == "test@example.com"

    def test_valid_output_with_no_contact_info(self) -> None:
        """Should accept output with None contact_info."""
        resume_content = "# Resume\n## Experience\nSome work history"
        output = ResumeGenerationOutput(
            content=resume_content,
            contact_info=None,
        )
        assert output.content == resume_content
        assert output.contact_info is None

    def test_markdown_content_format(self) -> None:
        """Should support markdown-formatted resume content."""
        markdown_resume = """# John Doe

## Skills
- Python, JavaScript, React

## Experience
### Software Engineer
2020-2024 at TechCorp
"""
        output = ResumeGenerationOutput(
            content=markdown_resume,
            contact_info=None,
        )
        assert output.content == markdown_resume
        assert "# John Doe" in output.content


class TestRefinementInput:
    """Validate RefinementInput contract."""

    def test_valid_input_with_markdown_resume_content(self) -> None:
        """Should accept markdown resume content as string."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            overall_score=0.85,
            semantic_score=0.88,
            keyword_coverage={},
        )
        resume_markdown = "# Resume\n## Experience\nSome content"
        input_data = RefinementInput(
            resume_content=resume_markdown,
            fit_assessment_output=fit_output,
            jd_content="Job description",
            user_id="user-123",
        )
        assert isinstance(input_data.resume_content, str)
        assert "Resume" in input_data.resume_content

    def test_fit_assessment_nesting(self) -> None:
        """Should properly nest FitAssessmentOutput."""
        fit_output = FitAssessmentOutput(
            fit_level="borderline",
            matches=[],
            gaps=[{"requirement": "10+ years", "type": "hard", "notes": ""}],
            terminology=[],
            overall_score=0.55,
            semantic_score=0.58,
            keyword_coverage={"experience": False},
        )
        input_data = RefinementInput(
            resume_content="# Resume\n## Skills\nPython, JavaScript",
            fit_assessment_output=fit_output,
            jd_content="JD text",
            user_id="user-123",
        )
        assert input_data.fit_assessment_output.fit_level == "borderline"
        assert len(input_data.fit_assessment_output.gaps) == 1


class TestRefinementOutput:
    """Validate RefinementOutput contract."""

    def test_valid_output_with_changes(self) -> None:
        """Should accept output with changes_made as list of strings."""
        output = RefinementOutput(
            refined_content="# Refined Resume\n## Experience\nUpdated content",
            changes_made=[
                "Added missing detail to Experience section",
                "Reordered skills by relevance to job requirements",
                "Adjusted phrasing to match job description terminology",
            ],
        )
        assert output.refined_content == "# Refined Resume\n## Experience\nUpdated content"
        assert len(output.changes_made) == 3
        assert "Added missing detail" in output.changes_made[0]

    def test_output_with_empty_changes_list(self) -> None:
        """Should accept output with empty changes_made list."""
        output = RefinementOutput(
            refined_content="Refined content",
            changes_made=[],
        )
        assert output.refined_content == "Refined content"
        assert len(output.changes_made) == 0
        assert isinstance(output.changes_made, list)

    def test_output_structure(self) -> None:
        """Should have exactly the required fields."""
        output = RefinementOutput(
            refined_content="# Refined Resume",
            changes_made=["Change 1", "Change 2"],
        )
        assert hasattr(output, "refined_content")
        assert hasattr(output, "changes_made")
        assert output.refined_content == "# Refined Resume"
        assert isinstance(output.changes_made, list)


class TestCrossStageDataFlow:
    """Validate data contracts across stage boundaries."""

    def test_fit_assessment_output_to_resume_generation_input(self) -> None:
        """Should flow FitAssessmentOutput → ResumeGenerationInput."""
        # Create fit assessment output
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[{"requirement": "Python", "priority": "required", "notes": ""}],
            gaps=[],
            terminology=[{"my_term": "REST", "jd_term": "REST API", "confidence": 0.9}],
            overall_score=0.85,
            semantic_score=0.88,
            keyword_coverage={"Python": True, "REST": True},
        )
        # Use as input to generation
        gen_input = ResumeGenerationInput(
            narratives_text="Background",
            fit_assessment_output=fit_output,
            contact_info=None,
            user_id="user-123",
        )
        assert gen_input.fit_assessment_output.fit_level == "strong"
        assert len(gen_input.fit_assessment_output.matches) == 1

    def test_fit_assessment_output_to_refinement_input(self) -> None:
        """Should flow FitAssessmentOutput → RefinementInput."""
        fit_output = FitAssessmentOutput(
            fit_level="moderate",
            matches=[],
            gaps=[{"requirement": "10+ years", "type": "hard", "notes": ""}],
            terminology=[],
            overall_score=0.65,
            semantic_score=0.68,
            keyword_coverage={"experience": False},
        )
        refinement_input = RefinementInput(
            resume_content="Resume text",
            fit_assessment_output=fit_output,
            jd_content="JD text",
            user_id="user-123",
        )
        assert refinement_input.fit_assessment_output.fit_level == "moderate"
        assert len(refinement_input.fit_assessment_output.gaps) == 1
