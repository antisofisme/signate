"""
Background Jobs API Routes

REST API endpoints for managing background jobs.
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ComputeEmbeddingsRequest(BaseModel):
    """Request to compute embeddings."""
    decision_ids: list[str] = Field(..., description="Decision IDs to compute embeddings for")
    force_recompute: bool = Field(False, description="Force recompute even if exists")


class GenerateDocumentRequest(BaseModel):
    """Request to generate a document in background."""
    doc_type: str
    title: Optional[str] = None
    domain_filter: Optional[str] = None
    scope_filter: Optional[str] = None
    max_decisions: int = 100
    notify_email: Optional[str] = None


class ExportDocumentRequest(BaseModel):
    """Request to export a document in background."""
    content: str
    title: str
    target: str  # confluence, notion, github_wiki
    config: dict[str, Any]


class JobResponse(BaseModel):
    """Response for job submission."""
    job_id: str
    status: str
    submitted_at: str


class JobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str
    status: str
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================


def _check_celery_available() -> bool:
    """Check if Celery is available."""
    try:
        from core.jobs.celery_app import celery_app
        # Check if broker is reachable
        return celery_app.control.ping(timeout=1.0) is not None
    except Exception:
        return False


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/status")
async def get_jobs_status():
    """
    Get the status of the background job system.
    """
    celery_available = _check_celery_available()

    return {
        "celery_available": celery_available,
        "queues": ["default", "embeddings", "documents", "exports", "analytics"] if celery_available else [],
    }


@router.post("/embeddings", response_model=JobResponse)
async def submit_embeddings_job(request: ComputeEmbeddingsRequest):
    """
    Submit a job to compute embeddings for decisions.
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from core.jobs.tasks import compute_embeddings_task

    result = compute_embeddings_task.delay(
        decision_ids=request.decision_ids,
        force_recompute=request.force_recompute,
    )

    return JobResponse(
        job_id=result.id,
        status="submitted",
        submitted_at=datetime.utcnow().isoformat(),
    )


@router.post("/reindex", response_model=JobResponse)
async def submit_reindex_job():
    """
    Submit a job to reindex all decisions.

    Warning: This is a heavy operation.
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from core.jobs.tasks import reindex_decisions_task

    result = reindex_decisions_task.delay()

    return JobResponse(
        job_id=result.id,
        status="submitted",
        submitted_at=datetime.utcnow().isoformat(),
    )


@router.post("/generate-document", response_model=JobResponse)
async def submit_document_generation_job(request: GenerateDocumentRequest):
    """
    Submit a job to generate a document in the background.
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from core.jobs.tasks import generate_document_task

    result = generate_document_task.delay(
        doc_type=request.doc_type,
        title=request.title,
        domain_filter=request.domain_filter,
        scope_filter=request.scope_filter,
        max_decisions=request.max_decisions,
        notify_email=request.notify_email,
    )

    return JobResponse(
        job_id=result.id,
        status="submitted",
        submitted_at=datetime.utcnow().isoformat(),
    )


@router.post("/export", response_model=JobResponse)
async def submit_export_job(request: ExportDocumentRequest):
    """
    Submit a job to export a document to an external platform.
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from core.jobs.tasks import export_document_task

    result = export_document_task.delay(
        content=request.content,
        title=request.title,
        target=request.target,
        config=request.config,
    )

    return JobResponse(
        job_id=result.id,
        status="submitted",
        submitted_at=datetime.utcnow().isoformat(),
    )


@router.post("/aggregate-analytics", response_model=JobResponse)
async def submit_analytics_aggregation_job():
    """
    Submit a job to aggregate analytics data.
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from core.jobs.tasks import aggregate_analytics_task

    result = aggregate_analytics_task.delay()

    return JobResponse(
        job_id=result.id,
        status="submitted",
        submitted_at=datetime.utcnow().isoformat(),
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status of a submitted job.
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from celery.result import AsyncResult
    from core.jobs.celery_app import celery_app

    result = AsyncResult(job_id, app=celery_app)

    response = JobStatusResponse(
        job_id=job_id,
        status=result.status,
    )

    if result.ready():
        if result.successful():
            response.result = result.result
        else:
            response.error = str(result.result)

    return response


@router.delete("/{job_id}")
async def revoke_job(job_id: str, terminate: bool = False):
    """
    Revoke a pending or running job.

    Args:
        job_id: The job ID to revoke
        terminate: If True, terminate even if running
    """
    if not _check_celery_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Background job system is not available"
        )

    from celery.result import AsyncResult
    from core.jobs.celery_app import celery_app

    result = AsyncResult(job_id, app=celery_app)
    result.revoke(terminate=terminate)

    return {"status": "revoked", "job_id": job_id}
