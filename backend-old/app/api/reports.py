"""
============================================================================
Reports API - PDF, Excel, CSV Export (Quick Wins Pattern)
============================================================================

Provides endpoints for generating and managing analytics reports.

Features:
- Generate reports in multiple formats (PDF, Excel, CSV)
- Async report generation with Celery
- Scheduled report generation
- Report history and management
- Download generated reports

Quick Wins Standards:
✅ StructuredLogger for consistent logging
✅ success_response wrapper for all responses
✅ Comprehensive error handling
✅ Celery integration for async processing
✅ Request ID tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from io import BytesIO
import math

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logging import StructuredLogger
from app.schemas.common import success_response, paginated_response, APIResponse, PaginatedAPIResponse
from app.schemas.report import (
    ReportGenerateRequest,
    ReportResponse,
    ReportScheduleRequest,
    ReportScheduleResponse,
    ReportTemplateResponse,
    QuickExportRequest
)
from app.services.report_service import ReportService
from app.models.user import User
from app.middleware.request_id import get_request_id

# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = StructuredLogger(__name__)

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/generate", response_model=APIResponse[ReportResponse], status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    request_data: ReportGenerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a report in specified format (async with Celery).

    Returns report metadata immediately and processes in background.
    Use the report ID to check status and download when ready.

    **Permissions:** Authenticated users only (admins for scheduled reports)

    **Process:**
    1. Validate request parameters
    2. Create report record in database
    3. Queue Celery task for async generation
    4. Return task ID and estimated time
    """
    request_id = get_request_id(request)

    logger.info(
        "Report generation requested",
        report_type=request_data.report_type,
        format=request_data.format,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)

        # Create report record
        report = await service.create_report(
            format=request_data.format,
            report_type=request_data.report_type,
            start_date=request_data.start_date,
            end_date=request_data.end_date,
            sections=request_data.sections,
            filters=request_data.filters or {}
        )

        # Start background generation with Celery
        task = await service.generate_report_async(report.id)

        logger.info(
            "Report generation task queued",
            report_id=str(report.id),
            task_id=task.id if hasattr(task, 'id') else None,
            request_id=request_id
        )

        response_data = ReportResponse(
            id=str(report.id),
            title=report.title,
            format=report.format,
            status=report.status,
            file_size=report.file_size,
            download_url=f"/api/reports/{report.id}/download" if report.status == "completed" else None,
            created_at=report.created_at,
            completed_at=report.completed_at,
            error_message=report.error_message,
            task_id=task.id if hasattr(task, 'id') else None,
            estimated_time="2-5 minutes"
        )

        return success_response(data=response_data, request_id=request_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to generate report",
            error=str(e),
            user_id=current_user.id,
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("", response_model=PaginatedAPIResponse[ReportResponse])
async def list_reports(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    format_filter: Optional[str] = Query(None, description="Filter by format"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all reports with pagination.

    **Permissions:** Authenticated users only

    **Filters:**
    - status_filter: pending, processing, completed, failed
    - format_filter: pdf, excel, csv
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing reports",
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        format_filter=format_filter,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        reports, total = await service.list_reports(
            page=page,
            page_size=page_size,
            status_filter=status_filter,
            format_filter=format_filter
        )

        report_responses = [
            ReportResponse(
                id=str(r.id),
                title=r.title,
                format=r.format,
                status=r.status,
                file_size=r.file_size,
                download_url=f"/api/reports/{r.id}/download" if r.status == "completed" else None,
                created_at=r.created_at,
                completed_at=r.completed_at,
                error_message=r.error_message,
                task_id=getattr(r, 'task_id', None),
                estimated_time=None
            )
            for r in reports
        ]

        logger.info(
            "Reports listed successfully",
            total=total,
            returned=len(report_responses),
            request_id=request_id
        )

        return paginated_response(
            data=report_responses,
            total=total,
            page=page,
            page_size=page_size,
            request_id=request_id
        )

    except Exception as e:
        logger.error(
            "Failed to list reports",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list reports: {str(e)}"
        )


@router.get("/{report_id}", response_model=APIResponse[ReportResponse])
async def get_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get report metadata by ID.

    **Permissions:** Authenticated users only
    """
    request_id = get_request_id(request)

    logger.info(
        "Getting report details",
        report_id=report_id,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        report = await service.get_report(report_id)

        if not report:
            logger.warning(
                "Report not found",
                report_id=report_id,
                request_id=request_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )

        response_data = ReportResponse(
            id=str(report.id),
            title=report.title,
            format=report.format,
            status=report.status,
            file_size=report.file_size,
            download_url=f"/api/reports/{report.id}/download" if report.status == "completed" else None,
            created_at=report.created_at,
            completed_at=report.completed_at,
            error_message=report.error_message,
            task_id=getattr(report, 'task_id', None),
            estimated_time=None
        )

        logger.info(
            "Report details retrieved",
            report_id=report_id,
            status=report.status,
            request_id=request_id
        )

        return success_response(data=response_data, request_id=request_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get report",
            report_id=report_id,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report: {str(e)}"
        )


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download generated report file.

    **Permissions:** Authenticated users only

    **Returns:** StreamingResponse with file download
    """
    request_id = get_request_id(request)

    logger.info(
        "Report download requested",
        report_id=report_id,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        report = await service.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )

        if report.status != "completed":
            logger.warning(
                "Report not ready for download",
                report_id=report_id,
                status=report.status,
                request_id=request_id
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Report is not ready. Status: {report.status}"
            )

        # Get report file
        file_data = await service.get_report_file(report_id)

        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report file not found"
            )

        # Determine media type
        media_types = {
            "pdf": "application/pdf",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "csv": "text/csv"
        }
        media_type = media_types.get(report.format, "application/octet-stream")

        # Generate filename
        filename = f"{report.title}.{report.format}"
        if report.format == "excel":
            filename = f"{report.title}.xlsx"

        logger.info(
            "Report download initiated",
            report_id=report_id,
            format=report.format,
            file_size=len(file_data),
            request_id=request_id
        )

        # Return file stream
        return StreamingResponse(
            BytesIO(file_data),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(file_data))
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to download report",
            report_id=report_id,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download report: {str(e)}"
        )


@router.delete("/{report_id}", response_model=APIResponse[dict])
async def delete_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a report and its associated file.

    **Permissions:** Authenticated users only (admins can delete any report)
    """
    request_id = get_request_id(request)

    logger.info(
        "Report deletion requested",
        report_id=report_id,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        success = await service.delete_report(report_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report not found: {report_id}"
            )

        logger.info(
            "Report deleted successfully",
            report_id=report_id,
            request_id=request_id
        )

        return success_response(
            data={"message": "Report deleted successfully", "report_id": report_id},
            request_id=request_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete report",
            report_id=report_id,
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}"
        )


@router.get("/templates/list", response_model=APIResponse[List[ReportTemplateResponse]])
async def list_report_templates(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List available report templates.

    **Permissions:** Authenticated users only
    """
    request_id = get_request_id(request)

    logger.info(
        "Listing report templates",
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        templates = await service.list_templates()

        logger.info(
            "Report templates listed",
            count=len(templates),
            request_id=request_id
        )

        return success_response(data=templates, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to list report templates",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list report templates: {str(e)}"
        )


@router.post("/schedule", response_model=APIResponse[ReportScheduleResponse], status_code=status.HTTP_201_CREATED)
async def schedule_report(
    schedule_data: ReportScheduleRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Schedule recurring report generation.

    **Permissions:** Admin users only
    """
    request_id = get_request_id(request)

    # Admin only
    if not current_user.is_superuser:
        logger.warning(
            "Unauthorized schedule attempt",
            user_id=current_user.id,
            request_id=request_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to schedule reports"
        )

    logger.info(
        "Report schedule creation requested",
        schedule_name=schedule_data.name,
        frequency=schedule_data.frequency,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        schedule = await service.create_schedule(
            name=schedule_data.name,
            report_type=schedule_data.report_type,
            format=schedule_data.format,
            sections=schedule_data.sections,
            frequency=schedule_data.frequency,
            time=schedule_data.time,
            recipients=schedule_data.recipients,
            is_active=schedule_data.is_active,
            filters=schedule_data.filters
        )

        logger.info(
            "Report schedule created",
            schedule_id=str(schedule.id),
            next_run=schedule.next_run,
            request_id=request_id
        )

        response_data = ReportScheduleResponse(
            id=str(schedule.id),
            name=schedule.name,
            report_type=schedule.report_type,
            format=schedule.format,
            sections=schedule.sections,
            frequency=schedule.frequency,
            time=schedule.time,
            recipients=schedule.recipients,
            is_active=schedule.is_active,
            last_run=schedule.last_run,
            next_run=schedule.next_run,
            created_at=schedule.created_at,
            filters=schedule.filters
        )

        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to create report schedule",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report schedule: {str(e)}"
        )


@router.get("/scheduled/list", response_model=APIResponse[List[ReportScheduleResponse]])
async def list_scheduled_reports(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all scheduled reports.

    **Permissions:** Admin users only
    """
    request_id = get_request_id(request)

    # Admin only
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required to view scheduled reports"
        )

    logger.info(
        "Listing scheduled reports",
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        schedules = await service.list_schedules()

        response_data = [
            ReportScheduleResponse(
                id=str(s.id),
                name=s.name,
                report_type=s.report_type,
                format=s.format,
                sections=s.sections,
                frequency=s.frequency,
                time=s.time,
                recipients=s.recipients,
                is_active=s.is_active,
                last_run=s.last_run,
                next_run=s.next_run,
                created_at=s.created_at,
                filters=s.filters
            )
            for s in schedules
        ]

        logger.info(
            "Scheduled reports listed",
            count=len(response_data),
            request_id=request_id
        )

        return success_response(data=response_data, request_id=request_id)

    except Exception as e:
        logger.error(
            "Failed to list scheduled reports",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list scheduled reports: {str(e)}"
        )


# ============================================================================
# Export Convenience Endpoints (Synchronous Quick Export)
# ============================================================================

@router.post("/export/csv")
async def export_csv(
    export_data: QuickExportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick export to CSV (synchronous).

    **Permissions:** Authenticated users only

    **Note:** For large datasets, use /generate endpoint instead
    """
    request_id = get_request_id(request)

    logger.info(
        "CSV export requested",
        start_date=export_data.start_date,
        end_date=export_data.end_date,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        buffer = await service.generate_csv_report(
            export_data.start_date,
            export_data.end_date,
            filters=export_data.filters
        )

        logger.info(
            "CSV export generated",
            file_size=buffer.getbuffer().nbytes,
            request_id=request_id
        )

        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="analytics_{export_data.start_date.strftime("%Y%m%d")}.csv"'
            }
        )

    except Exception as e:
        logger.error(
            "Failed to export CSV",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export CSV: {str(e)}"
        )


@router.post("/export/excel")
async def export_excel(
    export_data: QuickExportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick export to Excel (synchronous).

    **Permissions:** Authenticated users only

    **Note:** For large datasets, use /generate endpoint instead
    """
    request_id = get_request_id(request)

    logger.info(
        "Excel export requested",
        start_date=export_data.start_date,
        end_date=export_data.end_date,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        buffer = await service.generate_excel_report(
            export_data.start_date,
            export_data.end_date,
            filters=export_data.filters
        )

        logger.info(
            "Excel export generated",
            file_size=buffer.getbuffer().nbytes,
            request_id=request_id
        )

        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="analytics_{export_data.start_date.strftime("%Y%m%d")}.xlsx"'
            }
        )

    except Exception as e:
        logger.error(
            "Failed to export Excel",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export Excel: {str(e)}"
        )


@router.post("/export/pdf")
async def export_pdf(
    export_data: QuickExportRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Quick export to PDF (synchronous).

    **Permissions:** Authenticated users only

    **Note:** For large datasets, use /generate endpoint instead
    """
    request_id = get_request_id(request)

    logger.info(
        "PDF export requested",
        start_date=export_data.start_date,
        end_date=export_data.end_date,
        orientation=export_data.orientation,
        user_id=current_user.id,
        request_id=request_id
    )

    try:
        service = ReportService(db)
        buffer = await service.generate_pdf_report(
            export_data.start_date,
            export_data.end_date,
            orientation=export_data.orientation or "landscape",
            filters=export_data.filters
        )

        logger.info(
            "PDF export generated",
            file_size=buffer.getbuffer().nbytes,
            request_id=request_id
        )

        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="analytics_{export_data.start_date.strftime("%Y%m%d")}.pdf"'
            }
        )

    except Exception as e:
        logger.error(
            "Failed to export PDF",
            error=str(e),
            request_id=request_id,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export PDF: {str(e)}"
        )
