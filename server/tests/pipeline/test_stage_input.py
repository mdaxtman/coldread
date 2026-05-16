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
            FitAssessmentInput(
                narratives_text="text",
                user_id="user-123",
            )

    def test_missing_required_field_narratives_text(self) -> None:
        """Should reject missing narratives_text."""
        with pytest.raises(TypeError):
            FitAssessmentInput(
                jd_content="text",
                user_id="user-123",
            )

    def test_missing_required_field_user_id(self) -> None:
        """Should reject missing user_id."""
        with pytest.raises(TypeError):
            FitAssessmentInput(
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
            reasoning="Strong match on core skills",
        )
        assert output.fit_level == "strong"
        assert len(output.matches) == 1
        assert output.matches[0]["requirement"] == "Python"
        assert len(output.gaps) == 0
        assert len(output.terminology) == 0

    def test_fit_level_with_enum_values(self) -> None:
        """Should support all valid fit level values."""
        for level in ["strong", "moderate", "borderline", "poor"]:
            output = FitAssessmentOutput(
                fit_level=level,
                matches=[],
                gaps=[],
                terminology=[],
                reasoning="Test",
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
            reasoning="Test",
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
            reasoning="Test",
        )
        assert len(output.gaps) == 2
        assert output.gaps[0]["type"] == "hard"
        assert output.gaps[1]["type"] == "soft"

    def test_terminology_mappings(self) -> None:
        """Should support terminology mappings with confidence scores."""
        terminology = [
            {"my_term": "React", "jd_term": "React.js", "confidence": "0.95"},
            {"my_term": "REST API", "jd_term": "RESTful API", "confidence": "0.85"},
        ]
        output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=terminology,
            reasoning="Test",
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
            reasoning="Test",
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
        assert input_data.contact_info["email"] == "test@example.com"
        assert input_data.user_id == "user-123"

    def test_valid_input_without_contact_info(self) -> None:
        """Should accept valid input with contact_info as None."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            reasoning="Test",
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
            reasoning="Moderate fit",
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
        output = ResumeGenerationOutput(
            summary="Experienced engineer",
            experience=[
                {
                    "company": "TechCorp",
                    "title": "Senior Engineer",
                    "dates": "2020-2024",
                    "projects": [
                        {
                            "name": "Project A",
                            "dates": "2020-2021",
                            "bullets": ["Built feature X", "Shipped product Y"],
                        }
                    ],
                }
            ],
            skills=["Python", "React", "TypeScript"],
            contact={"email": "test@example.com", "linkedin": "linkedin.com/in/test"},
        )
        assert output.summary == "Experienced engineer"
        assert len(output.experience) == 1
        assert len(output.skills) == 3
        assert output.contact["email"] == "test@example.com"

    def test_optional_summary_and_contact(self) -> None:
        """Should accept output with None summary and contact."""
        output = ResumeGenerationOutput(
            summary=None,
            experience=[],
            skills=["Python"],
            contact=None,
        )
        assert output.summary is None
        assert output.contact is None
        assert len(output.skills) == 1

    def test_empty_experience_and_skills(self) -> None:
        """Should accept output with empty lists."""
        output = ResumeGenerationOutput(
            summary="Test",
            experience=[],
            skills=[],
            contact=None,
        )
        assert len(output.experience) == 0
        assert len(output.skills) == 0


class TestRefinementInput:
    """Validate RefinementInput contract."""

    def test_valid_input_with_dict_resume_content(self) -> None:
        """Should accept structured resume data as dict."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            reasoning="Test",
        )
        resume_content = {
            "summary": "Experienced",
            "experience": [],
            "skills": ["Python"],
        }
        input_data = RefinementInput(
            resume_content=resume_content,
            fit_assessment_output=fit_output,
            jd_content="Job description",
            user_id="user-123",
        )
        assert isinstance(input_data.resume_content, dict)
        assert input_data.resume_content["summary"] == "Experienced"

    def test_valid_input_with_string_resume_content(self) -> None:
        """Should accept markdown resume content as string."""
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[],
            gaps=[],
            terminology=[],
            reasoning="Test",
        )
        resume_markdown = "# Resume\n## Experience\n..."
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
            reasoning="Borderline fit",
        )
        input_data = RefinementInput(
            resume_content="Resume text",
            fit_assessment_output=fit_output,
            jd_content="JD text",
            user_id="user-123",
        )
        assert input_data.fit_assessment_output.fit_level == "borderline"
        assert len(input_data.fit_assessment_output.gaps) == 1


class TestRefinementOutput:
    """Validate RefinementOutput contract."""

    def test_valid_output_with_all_fields(self) -> None:
        """Should accept output with all optional fields."""
        output = RefinementOutput(
            refined_content="# Refined Resume\n...",
            changes_made=[
                {"section": "Experience", "change_description": "Added missing detail"},
                {"section": "Skills", "change_description": "Reordered by relevance"},
            ],
            remaining_gaps=[
                {"requirement": "10+ years", "why_unfixable": "Candidate lacks experience"}
            ],
        )
        assert output.refined_content == "# Refined Resume\n..."
        assert len(output.changes_made) == 2
        assert output.changes_made[0]["section"] == "Experience"
        assert len(output.remaining_gaps) == 1

    def test_output_with_none_optional_fields(self) -> None:
        """Should accept output with None for optional fields."""
        output = RefinementOutput(
            refined_content="Refined content",
            changes_made=None,
            remaining_gaps=None,
        )
        assert output.refined_content == "Refined content"
        assert output.changes_made is None
        assert output.remaining_gaps is None

    def test_output_with_empty_optional_lists(self) -> None:
        """Should accept output with empty lists for optional fields."""
        output = RefinementOutput(
            refined_content="Refined content",
            changes_made=[],
            remaining_gaps=[],
        )
        assert len(output.changes_made) == 0
        assert len(output.remaining_gaps) == 0


class TestCrossStageDataFlow:
    """Validate data contracts across stage boundaries."""

    def test_fit_assessment_output_to_resume_generation_input(self) -> None:
        """Should flow FitAssessmentOutput → ResumeGenerationInput."""
        # Create fit assessment output
        fit_output = FitAssessmentOutput(
            fit_level="strong",
            matches=[{"requirement": "Python", "priority": "required", "notes": ""}],
            gaps=[],
            terminology=[{"my_term": "REST", "jd_term": "REST API", "confidence": "0.9"}],
            reasoning="Strong match",
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
            reasoning="Moderate fit",
        )
        refinement_input = RefinementInput(
            resume_content="Resume text",
            fit_assessment_output=fit_output,
            jd_content="JD text",
            user_id="user-123",
        )
        assert refinement_input.fit_assessment_output.fit_level == "moderate"
        assert len(refinement_input.fit_assessment_output.gaps) == 1
