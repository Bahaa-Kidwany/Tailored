import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.core.database import get_session
from app.models.pipeline import (
    PipelineItemCreate,
    PipelineItemUpdate,
    PipelineItemResponse,
    PipelineMetricsResponse,
    OutreachPackageResponse,
    PipelineBatchImportRequest,
)
from app.pipeline.pipeline_service import pipeline_service
from app.ai.tailor.cv_fit_service import cv_fit_service
from app.ai.cover_letter.cover_letter_service import CoverLetterService
from app.schemas.cv_fit import CvFitCreateRequest, CoverLetterCreateRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("", response_model=List[PipelineItemResponse])
def list_pipeline_items(
    profile_id: Optional[int] = Query(default=None, description="Filter by candidate profile ID"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (saved, in_process, applied, etc.)"),
    q: Optional[str] = Query(default=None, description="Fuzzy search matching title, company, or recruiter email"),
    session: Session = Depends(get_session),
) -> List[PipelineItemResponse]:
    """
    Returns all jobs in the candidate's application pipeline.
    """
    return pipeline_service.get_pipeline_items(
        session=session, profile_id=profile_id, status=status_filter, search_query=q
    )


@router.get("/metrics", response_model=PipelineMetricsResponse)
def get_pipeline_metrics(
    profile_id: Optional[int] = Query(default=None, description="Filter by candidate profile ID"),
    session: Session = Depends(get_session),
) -> PipelineMetricsResponse:
    """
    Returns high-level application metrics (total, in_process, applied, with_email).
    """
    return pipeline_service.get_metrics(session=session, profile_id=profile_id)


@router.post("", response_model=PipelineItemResponse, status_code=status.HTTP_201_CREATED)
def add_job_to_pipeline(
    payload: PipelineItemCreate,
    session: Session = Depends(get_session),
) -> PipelineItemResponse:
    """
    Adds a job opportunity (Direct Email recruiter post or External Portal listing)
    to the candidate's unified Application Pipeline CRM.
    """
    try:
        item = pipeline_service.add_to_pipeline(session=session, item_in=payload)
        detail = pipeline_service.get_pipeline_item_detail(session=session, item_id=item.id)
        if not detail:
            raise HTTPException(status_code=500, detail="Failed to retrieve created pipeline item.")
        return detail
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.exception("Error adding job to pipeline")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{item_id}", response_model=PipelineItemResponse)
def get_pipeline_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> PipelineItemResponse:
    """
    Fetches a single pipeline item along with enriched job, tailored CV, and cover letter data.
    """
    detail = pipeline_service.get_pipeline_item_detail(session=session, item_id=item_id)
    if not detail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline item {item_id} not found.")
    return detail


@router.patch("/{item_id}", response_model=PipelineItemResponse)
def update_pipeline_item(
    item_id: int,
    payload: PipelineItemUpdate,
    session: Session = Depends(get_session),
) -> PipelineItemResponse:
    """
    Updates the status ('applied', 'interview', etc.), recruiter email, or notes for a pipeline item.
    Setting status to 'applied' automatically captures the applied_at timestamp.
    """
    updated = pipeline_service.update_pipeline_item(session=session, item_id=item_id, updates=payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline item {item_id} not found.")

    detail = pipeline_service.get_pipeline_item_detail(session=session, item_id=item_id)
    return detail


@router.delete("/{item_id}")
def delete_pipeline_item(
    item_id: int,
    session: Session = Depends(get_session),
):
    """
    Removes a job opportunity from the application pipeline.
    """
    success = pipeline_service.delete_pipeline_item(session=session, item_id=item_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline item {item_id} not found.")
    return {"success": True, "message": f"Pipeline item {item_id} successfully deleted."}


@router.get("/{item_id}/outreach", response_model=OutreachPackageResponse)
def get_outreach_package(
    item_id: int,
    session: Session = Depends(get_session),
) -> OutreachPackageResponse:
    """
    Generates pre-formatted 1-click outreach URLs (Gmail web and Mailto) and resolves
    tailored CV and cover letter attachments for instant recruiter email dispatch.
    """
    package = pipeline_service.generate_outreach_package(session=session, item_id=item_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline item {item_id} not found.")
    return package


@router.post("/{item_id}/tailor-cv", response_model=PipelineItemResponse)
def tailor_cv_for_pipeline_item(
    item_id: int,
    persona_id: Optional[str] = Query(default=None),
    user_comments: Optional[str] = Query(default=None),
    session: Session = Depends(get_session),
) -> PipelineItemResponse:
    """
    Shortcut: Triggers tailored CV generation for this pipeline job and automatically
    links the resulting document to the pipeline item.
    """
    detail = pipeline_service.get_pipeline_item_detail(session=session, item_id=item_id)
    if not detail or not detail.job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline item {item_id} not found.")

    try:
        cv_req = CvFitCreateRequest(
            profile_id=detail.profile_id,
            persona_id=persona_id,
            job_id=detail.job_id,
            job_title=detail.job.get("title"),
            company_name=detail.job.get("company_name"),
            job_description_text=detail.job.get("raw_description"),
            parsed_skills=detail.job.get("parsed_skills"),
            fit_score=detail.job.get("fit_score"),
            user_comments=user_comments,
        )
        cv_res = cv_fit_service.create_cv_fit(cv_req)
        pipeline_service.update_pipeline_item(
            session=session,
            item_id=item_id,
            updates=PipelineItemUpdate(tailored_cv_doc_id=cv_res.doc_id),
        )
        return pipeline_service.get_pipeline_item_detail(session=session, item_id=item_id)
    except Exception as exc:
        logger.exception("Error tailoring CV for pipeline item")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{item_id}/cover-letter", response_model=PipelineItemResponse)
def generate_cover_letter_for_pipeline_item(
    item_id: int,
    session: Session = Depends(get_session),
) -> PipelineItemResponse:
    """
    Shortcut: Generates a tailored cover letter for this pipeline job and automatically
    links the resulting document to the pipeline item.
    """
    detail = pipeline_service.get_pipeline_item_detail(session=session, item_id=item_id)
    if not detail or not detail.job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pipeline item {item_id} not found.")

    try:
        cl_service = CoverLetterService()
        cl_req = CoverLetterCreateRequest(
            job_id=detail.job_id,
            job_title=detail.job.get("title"),
            company_name=detail.job.get("company_name"),
            job_description_text=detail.job.get("raw_description"),
            base_cv_text="Extracted candidate experience aligned with engineering and data systems.",
        )
        cl_res = cl_service.generate_cover_letter(cl_req)
        pipeline_service.update_pipeline_item(
            session=session,
            item_id=item_id,
            updates=PipelineItemUpdate(cover_letter_doc_id=cl_res.doc_id),
        )
        return pipeline_service.get_pipeline_item_detail(session=session, item_id=item_id)
    except Exception as exc:
        logger.exception("Error generating cover letter for pipeline item")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/batch-import", response_model=List[PipelineItemResponse])
def batch_import_pipeline_items(
    payload: PipelineBatchImportRequest,
    session: Session = Depends(get_session),
) -> List[PipelineItemResponse]:
    """
    Migrates pipeline items from client localStorage into the server database.
    """
    return pipeline_service.batch_import(session=session, request=payload)

