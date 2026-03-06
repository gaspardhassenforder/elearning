"""In-memory tracker for async quiz generation jobs.

Quiz generation doesn't use surreal-commands, so we track job state here.
The frontend polls /api/commands/jobs/{job_id} which checks this store for
quizjob-* prefixed IDs.
"""

import uuid
from typing import Any, Dict, Optional

_jobs: Dict[str, Dict[str, Any]] = {}

QUIZ_JOB_PREFIX = "quizjob-"


def create_quiz_job() -> str:
    job_id = f"{QUIZ_JOB_PREFIX}{uuid.uuid4().hex[:12]}"
    _jobs[job_id] = {"status": "processing", "result": None, "error_message": None}
    return job_id


def complete_quiz_job(job_id: str, quiz_id: str, surface_data: Optional[Dict[str, Any]] = None) -> None:
    if job_id in _jobs:
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = surface_data or {"quiz_id": quiz_id}


def fail_quiz_job(job_id: str, error: str) -> None:
    if job_id in _jobs:
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error_message"] = error


def get_quiz_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(job_id)


def is_quiz_job(job_id: str) -> bool:
    return job_id.startswith(QUIZ_JOB_PREFIX)
