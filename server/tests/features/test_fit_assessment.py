from unittest.mock import patch

from features.fit_assessment import run_fit_assessment_workflow


def test_run_fit_assessment_workflow_full_path() -> None:
    """Verify fit assessment workflow loads DB, calls pipeline, and saves results."""
    with (
        patch("features.fit_assessment.job_descriptions.get_jd") as mock_get_jd,
        patch("features.fit_assessment.narratives.list_narratives") as mock_narratives,
        patch("features.fit_assessment.fit_reports.create_fit_report") as mock_create,
        patch("features.fit_assessment.analyze_jd_for_injection"),
        patch("features.fit_assessment.run_fit_assessment") as mock_fit,
    ):
        mock_get_jd.return_value = {"id": "jd-1", "content": "JD text"}
        mock_narratives.return_value = [
            {
                "title": "Role",
                "content": "Experience",
                "category": "role",
            }
        ]
        mock_fit.return_value = {
            "fit_level": "strong",
            "matches": [],
            "gaps": [],
            "terminology": [],
            "reasoning": "Good fit",
        }
        mock_create.return_value = {"id": "report-1"}

        result = run_fit_assessment_workflow(jd_id="jd-1", user_id="user-1")

        assert result["id"] == "report-1"
        mock_fit.assert_called_once()
        mock_create.assert_called_once()
