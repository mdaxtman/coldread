"""Tests for async job queue API endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestFitAssessmentQueueing:
    """Tests for POST /jobs/fit-assessment/{jd_id} endpoint."""

    def test_fit_assessment_endpoint_queues_job(self) -> None:
        """Test that fit assessment endpoint queues a job and returns immediately."""
        # First create a JD to use
        jd_response = client.post("/jds", json={"content": "Test job description"})
        assert jd_response.status_code == 201
        jd_id = jd_response.json()["id"]

        # Queue a fit assessment job
        response = client.post(f"/jobs/fit-assessment/{jd_id}")

        assert response.status_code == 202
        result = response.json()
        assert "jobId" in result  # camelCase response
        assert result["status"] == "pending"
        assert result["jobType"] == "fit_assessment"
        assert "createdAt" in result
        assert result["metadata"]["jd_id"] == jd_id

    def test_fit_assessment_endpoint_returns_job_id(self) -> None:
        """Test that response includes a valid job_id."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        response = client.post(f"/jobs/fit-assessment/{jd_id}")

        result = response.json()
        job_id = result["jobId"]
        # Job ID should be a valid UUID string
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_fit_assessment_endpoint_fails_with_nonexistent_jd(self) -> None:
        """Test that endpoint returns 404 for nonexistent JD."""
        response = client.post("/jobs/fit-assessment/nonexistent-jd-id")

        assert response.status_code == 404
        assert response.json()["detail"] == "Job description not found"

    def test_fit_assessment_endpoint_includes_metadata(self) -> None:
        """Test that job metadata includes the JD ID."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        response = client.post(f"/jobs/fit-assessment/{jd_id}")

        result = response.json()
        assert result["metadata"]["jd_id"] == jd_id


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
        # Create a JD and run fit assessment to get a fit report
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        fit_response = client.post(f"/jds/{jd_id}/fit")
        assert fit_response.status_code == 201
        fit_report_id = fit_response.json()["id"]

        # Queue resume generation
        response = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": fit_report_id},
        )

        assert response.status_code == 202
        result = response.json()
        assert result["status"] == "pending"
        assert result["jobType"] == "resume_generation"
        assert result["metadata"]["fit_report_id"] == fit_report_id
        assert result["metadata"]["jd_id"] == jd_id

    def test_resume_generation_endpoint_returns_job_id(self) -> None:
        """Test that resume generation response includes a valid job_id."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        fit_response = client.post(f"/jds/{jd_id}/fit")
        fit_report_id = fit_response.json()["id"]

        response = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": fit_report_id},
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
            "/jobs/refinement/variant-123",
            json={"fitReportId": "nonexistent-fit-report"},
        )

        assert response.status_code == 404
        assert "Fit report not found" in response.json()["detail"]

    def test_refinement_endpoint_queues_job(self) -> None:
        """Test that refinement endpoint queues a job."""
        # Create a JD, fit report, and resume variant
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        fit_response = client.post(f"/jds/{jd_id}/fit")
        fit_report_id = fit_response.json()["id"]

        resume_response = client.post(
            f"/jds/{jd_id}/resume",
            json={"fitReportId": fit_report_id},
        )
        assert resume_response.status_code == 201
        variant_id = resume_response.json()["id"]

        # Queue refinement
        response = client.post(
            f"/jobs/refinement/{variant_id}",
            json={"fitReportId": fit_report_id},
        )

        assert response.status_code == 202
        result = response.json()
        assert result["status"] == "pending"
        assert result["jobType"] == "refinement"
        assert result["metadata"]["fit_report_id"] == fit_report_id
        assert result["metadata"]["variant_id"] == variant_id

    def test_refinement_endpoint_returns_job_id(self) -> None:
        """Test that refinement response includes a valid job_id."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        fit_response = client.post(f"/jds/{jd_id}/fit")
        fit_report_id = fit_response.json()["id"]

        resume_response = client.post(
            f"/jds/{jd_id}/resume",
            json={"fitReportId": fit_report_id},
        )
        variant_id = resume_response.json()["id"]

        response = client.post(
            f"/jobs/refinement/{variant_id}",
            json={"fitReportId": fit_report_id},
        )

        result = response.json()
        job_id = result["jobId"]
        assert isinstance(job_id, str)
        assert len(job_id) > 0


class TestJobStatusEndpoint:
    """Tests for GET /jobs/{job_id} endpoint."""

    def test_get_job_returns_pending_job(self) -> None:
        """Test that get_job returns the status of a pending job."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        queue_response = client.post(f"/jobs/fit-assessment/{jd_id}")
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
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        queue_response = client.post(f"/jobs/fit-assessment/{jd_id}")
        job_id = queue_response.json()["jobId"]

        response = client.get(f"/jobs/{job_id}")

        result = response.json()
        assert result["metadata"]["jd_id"] == jd_id

    def test_get_job_includes_created_at(self) -> None:
        """Test that get_job includes the created_at timestamp."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        queue_response = client.post(f"/jobs/fit-assessment/{jd_id}")
        job_id = queue_response.json()["jobId"]

        response = client.get(f"/jobs/{job_id}")

        result = response.json()
        assert "createdAt" in result
        # Should be parseable as ISO datetime
        datetime.fromisoformat(result["createdAt"])


class TestResponseFormats:
    """Tests for API response format consistency."""

    def test_job_response_uses_camel_case(self) -> None:
        """Test that job responses use camelCase for field names."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        response = client.post(f"/jobs/fit-assessment/{jd_id}")

        result = response.json()
        # Should use camelCase
        assert "jobId" in result
        assert "jobType" in result
        assert "createdAt" in result
        # Should NOT have snake_case versions
        assert "job_id" not in result
        assert "job_type" not in result
        assert "created_at" not in result

    def test_all_job_endpoints_return_same_format(self) -> None:
        """Test that all job endpoints return the same response format."""
        jd_response = client.post("/jds", json={"content": "Test job description"})
        jd_id = jd_response.json()["id"]

        # Queue a fit assessment
        fit_queue_response = client.post(f"/jobs/fit-assessment/{jd_id}")
        fit_queue_result = fit_queue_response.json()

        fit_response = client.post(f"/jds/{jd_id}/fit")
        fit_report_id = fit_response.json()["id"]

        # Queue resume generation
        resume_queue_response = client.post(
            "/jobs/resume-generation",
            json={"fitReportId": fit_report_id},
        )
        resume_queue_result = resume_queue_response.json()

        # Both should have the same fields
        expected_fields = {"jobId", "jobType", "status", "createdAt", "metadata"}
        assert set(fit_queue_result.keys()) == expected_fields
        assert set(resume_queue_result.keys()) == expected_fields
