"""Job models and queue system."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(str, Enum):
    """Pipeline job types."""

    FIT_ASSESSMENT = "fit_assessment"
    RESUME_GENERATION = "resume_generation"
    REFINEMENT = "refinement"


@dataclass
class Job:
    """Represents an async job in the pipeline."""

    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType = field(default=JobType.FIT_ASSESSMENT)
    user_id: str = field(default="")
    status: JobStatus = field(default=JobStatus.PENDING)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, job_type: str | JobType, user_id: str, **metadata: Any) -> "Job":
        """Create a new job.

        Args:
            job_type: Type of job to create
            user_id: Current user ID
            **metadata: Additional metadata to store with job

        Returns:
            New Job instance
        """
        if isinstance(job_type, str):
            job_type = JobType(job_type)

        job = cls(
            job_type=job_type,
            user_id=user_id,
            metadata=metadata,
        )
        return job

    def to_dict(self) -> dict[str, Any]:
        """Serialize job to dictionary."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "user_id": self.user_id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class JobQueue:
    """In-memory job queue for async processing."""

    def __init__(self) -> None:
        """Initialize job queue."""
        self._jobs: dict[str, Job] = {}
        self._pending: list[Job] = []

    def add_job(self, job: Job) -> Job:
        """Add a job to the queue.

        Args:
            job: Job to add

        Returns:
            The added job
        """
        self._jobs[job.job_id] = job
        self._pending.append(job)
        return job

    def get_job(self, job_id: str) -> Job | None:
        """Retrieve a job by ID.

        Args:
            job_id: Job ID to retrieve

        Returns:
            Job if found, None otherwise
        """
        return self._jobs.get(job_id)

    def get_pending_jobs(self) -> list[Job]:
        """Get list of pending jobs.

        Returns:
            List of pending jobs
        """
        return [j for j in self._pending if j.status == JobStatus.PENDING]

    def mark_processing(self, job_id: str) -> bool:
        """Mark a job as processing.

        Args:
            job_id: Job ID to mark

        Returns:
            True if successful, False if job not found
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.PROCESSING
            return True
        return False

    def mark_completed(self, job_id: str) -> bool:
        """Mark a job as completed.

        Args:
            job_id: Job ID to mark

        Returns:
            True if successful, False if job not found
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            # Remove from pending list
            self._pending = [j for j in self._pending if j.job_id != job_id]
            return True
        return False

    def mark_failed(self, job_id: str) -> bool:
        """Mark a job as failed.

        Args:
            job_id: Job ID to mark

        Returns:
            True if successful, False if job not found
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            # Remove from pending list
            self._pending = [j for j in self._pending if j.job_id != job_id]
            return True
        return False
