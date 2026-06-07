"""Tests for async job queue API endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient

from main import app
from tests.integration.conftest import SAMPLE_FIT_REPORT, SAMPLE_JD

client = TestClient(app)

JD_ID = SAMPLE_JD["id"]
FIT_REPORT_ID = SAMPLE_FIT_REPORT["id"]
VARIANT_ID = "00000000-0000-0000-0000-000000000040"


class TestFitAssessmentQueueing:
    """Tests for POST /jobs/fit-assessment/{jd_id} endpoint."""

    def test_fit_assessment_endpoint_queues_job(self) -> None:
        """Test that fit assessment endpoint queues a job and returns immediately."""
        response = client.post(f"/jobs/fit-assessment/{JD_ID}")

        assert response.status_code == 202
        result = response.json()
        assert "jobId" in result
        assert result["status"] == "pending"
        assert result["jobType"] == "fit_assessment"
        assert "createdAt" in result
        assert result["metadata"]["jd_id"] == JD_ID

    def test_fit_assessment_endpoint_returns_job_id(self) -> None:
        """Test that response includes a valid job_id."""
        response = client.post(f"/jobs/fit-assessment/{JD_ID}")

        result = response.json()
        job_id = result["jobId"]
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_fit_assessment_endpoint_fails_with_nonexistent_jd(self) -> None:
        """Test that endpoint returns 404 for nonexistent JD."""
        response = client.post("/jobs/fit-assessment/nonexistent-jd-id")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job description not found"

    def test_fit_assessment_endpoint_includes_metadata(self) -> None:
        """Test that job metadata includes the JD ID."""
        response = client.post(f"/jobs/fit-assessment/{JD_ID}")

        result = response.json()
        assert result["metadata"]["jd_id"] == JD_ID


class TestResumeGenerationQueueing:
    """Tests for POST /jobs/resume-generation endpoint."""

    def test_resume_generation_endpoint_requires_fit_report(self) -> None:
        """Test that resume generation requires a valid fit report ID."""
        response = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": "nonexistent-fit-report"},
        )

        assert response.status_code == 404
        assert "Fit report not found" in response.json()["detail"]

    def test_resume_generation_endpoint_queues_job_with_fit_report(self) -> None:
        """Test that resume generation endpoint queues a job with fit report metadata."""
        response = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": FIT_REPORT_ID},
        )

        assert response.status_code == 202
        result = response.json()
        assert result["status"] == "pending"
        assert result["jobType"] == "resume_generation"
        assert result["metadata"]["fit_report_id"] == FIT_REPORT_ID
        assert result["metadata"]["jd_id"] == JD_ID

    def test_resume_generation_endpoint_returns_job_id(self) -> None:
        """Test that resume generation response includes a valid job_id."""
        response = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": FIT_REPORT_ID},
        )

        result = response.json()
        job_id = result["jobId"]
        assert isinstance(job_id, str)
        assert len(job_id) > 0


class TestRefinementQueueing:
    """Tests for POST /jobs/refinement/{variant_id} endpoint."""

    def test_refinement_endpoint_requires_fit_report(self) -> None:
        """Test that refinement requires a valid fit report ID."""
        response = client.post(
            f"/jobs/refinement/{VARIANT_ID}",
            json={"fitReportId": "nonexistent-fit-report"},
        )

        assert response.status_code == 404
        assert "Fit report not found" in response.json()["detail"]

    def test_refinement_endpoint_queues_job(self) -> None:
        """Test that refinement endpoint queues a job."""
        response = client.post(
            f"/jobs/refinement/{VARIANT_ID}",
            json={"fitReportId": FIT_REPORT_ID},
        )

        assert response.status_code == 202
        result = response.json()
        assert result["status"] == "pending"
        assert result["jobType"] == "refinement"
        assert result["metadata"]["fit_report_id"] == FIT_REPORT_ID
        assert result["metadata"]["variant_id"] == VARIANT_ID

    def test_refinement_endpoint_returns_job_id(self) -> None:
        """Test that refinement response includes a valid job_id."""
        response = client.post(
            f"/jobs/refinement/{VARIANT_ID}",
            json={"fitReportId": FIT_REPORT_ID},
        )

        result = response.json()
        job_id = result["jobId"]
        assert isinstance(job_id, str)
        assert len(job_id) > 0


class TestJobStatusEndpoint:
    """Tests for GET /jobs/{job_id} endpoint."""

    def test_get_job_returns_pending_job(self) -> None:
        """Test that get_job returns the status of a pending job."""
        queue_response = client.post(f"/jobs/fit-assessment/{JD_ID}")
        job_id = queue_response.json()["jobId"]

        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["jobId"] == job_id
        assert result["status"] == "pending"
        assert result["jobType"] == "fit_assessment"

    def test_get_job_fails_with_nonexistent_job(self) -> None:
        """Test that get_job returns 404 for nonexistent job."""
        response = client.get("/jobs/nonexistent-job-id")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]

    def test_get_job_returns_job_metadata(self) -> None:
        """Test that get_job returns the job's metadata."""
        queue_response = client.post(f"/jobs/fit-assessment/{JD_ID}")
        job_id = queue_response.json()["jobId"]

        response = client.get(f"/jobs/{job_id}")

        result = response.json()
        assert result["metadata"]["jd_id"] == JD_ID

    def test_get_job_includes_created_at(self) -> None:
        """Test that get_job includes the created_at timestamp."""
        queue_response = client.post(f"/jobs/fit-assessment/{JD_ID}")
        job_id = queue_response.json()["jobId"]

        response = client.get(f"/jobs/{job_id}")

        result = response.json()
        assert "createdAt" in result
        datetime.fromisoformat(result["createdAt"])


class TestResponseFormats:
    """Tests for API response format consistency."""

    def test_job_response_uses_camel_case(self) -> None:
        """Test that job responses use camelCase for field names."""
        response = client.post(f"/jobs/fit-assessment/{JD_ID}")

        result = response.json()
        assert "jobId" in result
        assert "jobType" in result
        assert "createdAt" in result
        assert "job_id" not in result
        assert "job_type" not in result
        assert "created_at" not in result

    def test_all_job_endpoints_return_same_format(self) -> None:
        """Test that all job endpoints return the same response format."""
        fit_queue_result = client.post(f"/jobs/fit-assessment/{JD_ID}").json()
        resume_queue_result = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": FIT_REPORT_ID},
        ).json()

        expected_fields = {"jobId", "jobType", "status", "createdAt", "metadata"}
        assert set(fit_queue_result.keys()) == expected_fields
        assert set(resume_queue_result.keys()) == expected_fields
