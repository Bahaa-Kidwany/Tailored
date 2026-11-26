import re
import urllib.parse
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select

from app.models.job import JobDB
from app.models.document import GeneratedDocumentDB
from app.models.profile import UserProfileDB
from app.models.pipeline import (
    PipelineItemDB,
    PipelineItemCreate,
    PipelineItemUpdate,
    PipelineItemResponse,
    PipelineMetricsResponse,
    OutreachPackageResponse,
    PipelineBatchImportRequest,
    utc_now,
)
from app.api.routes.jobs import format_job_response, extract_recruiter_email


def is_eligible_for_pipeline(job: JobDB) -> bool:
    """
    Unified Multi-Channel Pipeline rule:
    All valid job opportunities (Direct Email recruiter posts AND External Portal listings)
    can be tracked in the Application Pipeline CRM.
    """
    return bool(job)


class PipelineService:
    @staticmethod
    def is_eligible(job: JobDB) -> bool:
        return is_eligible_for_pipeline(job)

    def add_to_pipeline(self, session: Session, item_in: PipelineItemCreate) -> PipelineItemDB:
        job = session.get(JobDB, item_in.job_id)
        if not job:
            raise ValueError(f"Job with ID {item_in.job_id} does not exist.")

        if not self.is_eligible(job):
            raise ValueError(
                f"Job '{job.title}' ({job.source_id}) is a standard listing and cannot be added to the pipeline. "
                "Only recruiter posts and custom descriptions are eligible."
            )

        # Check for existing pipeline item for this job
        stmt = select(PipelineItemDB).where(PipelineItemDB.job_id == item_in.job_id)
        if item_in.profile_id is not None:
            stmt = stmt.where(PipelineItemDB.profile_id == item_in.profile_id)
        existing = session.exec(stmt).first()

        recruiter_email = item_in.recruiter_email or extract_recruiter_email(job.raw_description)

        if existing:
            # Update existing item with new status or email if provided
            if item_in.status:
                existing.status = item_in.status
            if recruiter_email and not existing.recruiter_email:
                existing.recruiter_email = recruiter_email
            if item_in.notes:
                existing.notes = item_in.notes
            existing.updated_at = utc_now()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing

        # Create new pipeline item
        status = item_in.status or ("in_process" if recruiter_email else "saved")
        new_item = PipelineItemDB(
            profile_id=item_in.profile_id,
            job_id=item_in.job_id,
            status=status,
            recruiter_email=recruiter_email,
            notes=item_in.notes,
            saved_at=utc_now(),
        )
        session.add(new_item)
        session.commit()
        session.refresh(new_item)
        return new_item

    def get_pipeline_items(
        self,
        session: Session,
        profile_id: Optional[int] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[PipelineItemResponse]:
        stmt = select(PipelineItemDB)
        if profile_id is not None:
            stmt = stmt.where(PipelineItemDB.profile_id == profile_id)
        if status:
            stmt = stmt.where(PipelineItemDB.status == status)

        stmt = stmt.order_by(PipelineItemDB.saved_at.desc())
        items = session.exec(stmt).all()

        results: List[PipelineItemResponse] = []
        q = (search_query or "").strip().lower()

        for item in items:
            job = session.get(JobDB, item.job_id)
            if not job or not self.is_eligible(job):
                continue

            job_dict = format_job_response(job).model_dump()

            # Filter by search query across title, company, recruiter email
            if q:
                match_title = q in (job.title or "").lower()
                match_comp = q in (job.company_name or "").lower()
                match_email = q in (item.recruiter_email or "").lower()
                if not (match_title or match_comp or match_email):
                    continue

            # Look up linked tailored CV document if present
            tailored_cv_dict: Optional[Dict[str, Any]] = None
            if item.tailored_cv_doc_id:
                cv_doc = session.exec(
                    select(GeneratedDocumentDB).where(GeneratedDocumentDB.doc_id == item.tailored_cv_doc_id)
                ).first()
                if cv_doc:
                    tailored_cv_dict = {
                        "doc_id": cv_doc.doc_id,
                        "compile_status": cv_doc.compile_status,
                        "created_at": cv_doc.created_at.isoformat(),
                    }

            # Look up linked cover letter if present
            cover_letter_dict: Optional[Dict[str, Any]] = None
            if item.cover_letter_doc_id:
                cl_doc = session.exec(
                    select(GeneratedDocumentDB).where(GeneratedDocumentDB.doc_id == item.cover_letter_doc_id)
                ).first()
                if cl_doc:
                    cover_letter_dict = {
                        "doc_id": cl_doc.doc_id,
                        "subject_line": f"Application for {job.title} - {job.company_name}",
                        "body_markdown": cl_doc.content_text or "",
                        "created_at": cl_doc.created_at.isoformat(),
                    }

            results.append(
                PipelineItemResponse(
                    id=item.id,
                    profile_id=item.profile_id,
                    job_id=item.job_id,
                    status=item.status,
                    recruiter_email=item.recruiter_email,
                    notes=item.notes,
                    tailored_cv_doc_id=item.tailored_cv_doc_id,
                    cover_letter_doc_id=item.cover_letter_doc_id,
                    saved_at=item.saved_at.isoformat() if item.saved_at else "",
                    applied_at=item.applied_at.isoformat() if item.applied_at else None,
                    created_at=item.created_at.isoformat() if item.created_at else "",
                    updated_at=item.updated_at.isoformat() if item.updated_at else "",
                    job=job_dict,
                    tailored_cv=tailored_cv_dict,
                    cover_letter=cover_letter_dict,
                )
            )

        return results

    def get_pipeline_item_detail(self, session: Session, item_id: int) -> Optional[PipelineItemResponse]:
        item = session.get(PipelineItemDB, item_id)
        if not item:
            return None

        job = session.get(JobDB, item.job_id)
        job_dict = format_job_response(job).model_dump() if job else None

        tailored_cv_dict: Optional[Dict[str, Any]] = None
        if item.tailored_cv_doc_id:
            cv_doc = session.exec(
                select(GeneratedDocumentDB).where(GeneratedDocumentDB.doc_id == item.tailored_cv_doc_id)
            ).first()
            if cv_doc:
                tailored_cv_dict = {
                    "doc_id": cv_doc.doc_id,
                    "compile_status": cv_doc.compile_status,
                    "created_at": cv_doc.created_at.isoformat(),
                }

        cover_letter_dict: Optional[Dict[str, Any]] = None
        if item.cover_letter_doc_id:
            cl_doc = session.exec(
                select(GeneratedDocumentDB).where(GeneratedDocumentDB.doc_id == item.cover_letter_doc_id)
            ).first()
            if cl_doc:
                cover_letter_dict = {
                    "doc_id": cl_doc.doc_id,
                    "subject_line": f"Application for {job.title if job else 'Role'} - {job.company_name if job else 'Company'}",
                    "body_markdown": cl_doc.content_text or "",
                    "created_at": cl_doc.created_at.isoformat(),
                }

        return PipelineItemResponse(
            id=item.id,
            profile_id=item.profile_id,
            job_id=item.job_id,
            status=item.status,
            recruiter_email=item.recruiter_email,
            notes=item.notes,
            tailored_cv_doc_id=item.tailored_cv_doc_id,
            cover_letter_doc_id=item.cover_letter_doc_id,
            saved_at=item.saved_at.isoformat() if item.saved_at else "",
            applied_at=item.applied_at.isoformat() if item.applied_at else None,
            created_at=item.created_at.isoformat() if item.created_at else "",
            updated_at=item.updated_at.isoformat() if item.updated_at else "",
            job=job_dict,
            tailored_cv=tailored_cv_dict,
            cover_letter=cover_letter_dict,
        )

    def update_pipeline_item(
        self, session: Session, item_id: int, updates: PipelineItemUpdate
    ) -> Optional[PipelineItemDB]:
        item = session.get(PipelineItemDB, item_id)
        if not item:
            return None

        if updates.status is not None:
            old_status = item.status
            item.status = updates.status
            if updates.status == "applied" and not item.applied_at:
                item.applied_at = utc_now()
            elif updates.status != "applied" and old_status == "applied" and updates.applied_at is None:
                item.applied_at = None

        if updates.applied_at is not None:
            item.applied_at = updates.applied_at
        if updates.recruiter_email is not None:
            item.recruiter_email = updates.recruiter_email
        if updates.notes is not None:
            item.notes = updates.notes
        if updates.tailored_cv_doc_id is not None:
            item.tailored_cv_doc_id = updates.tailored_cv_doc_id
        if updates.cover_letter_doc_id is not None:
            item.cover_letter_doc_id = updates.cover_letter_doc_id

        item.updated_at = utc_now()
        session.add(item)
        session.commit()
        session.refresh(item)
        return item

    def delete_pipeline_item(self, session: Session, item_id: int) -> bool:
        item = session.get(PipelineItemDB, item_id)
        if not item:
            return False
        session.delete(item)
        session.commit()
        return True

    def get_metrics(self, session: Session, profile_id: Optional[int] = None) -> PipelineMetricsResponse:
        stmt = select(PipelineItemDB)
        if profile_id is not None:
            stmt = stmt.where(PipelineItemDB.profile_id == profile_id)
        all_items = session.exec(stmt).all()

        metrics = PipelineMetricsResponse()
        valid_items: List[PipelineItemDB] = []
        for it in all_items:
            job = session.get(JobDB, it.job_id)
            if job and self.is_eligible(job):
                valid_items.append(it)

        metrics.total = len(valid_items)
        metrics.in_process = sum(1 for i in valid_items if i.status == "in_process")
        metrics.applied = sum(1 for i in valid_items if i.status == "applied")
        metrics.interview = sum(1 for i in valid_items if i.status == "interview")
        metrics.saved = sum(1 for i in valid_items if i.status == "saved")
        metrics.archived = sum(1 for i in valid_items if i.status == "archived")
        metrics.with_email = sum(1 for i in valid_items if bool(i.recruiter_email))

        return metrics

    def generate_outreach_package(self, session: Session, item_id: int) -> Optional[OutreachPackageResponse]:
        item = session.get(PipelineItemDB, item_id)
        if not item:
            return None

        job = session.get(JobDB, item.job_id)
        if not job:
            return None

        # Look up candidate profile
        candidate_name = "Candidate"
        candidate_email = ""
        candidate_phone = ""
        if item.profile_id:
            profile = session.get(UserProfileDB, item.profile_id)
            if profile:
                candidate_name = profile.full_name or "Candidate"
                candidate_email = profile.primary_email or ""
                if hasattr(profile, "contact_numbers") and profile.contact_numbers:
                    candidate_phone = profile.contact_numbers[0].phone_number

        role = job.title or "Position"
        company = job.company_name or "Hiring Team"
        to_email = item.recruiter_email or extract_recruiter_email(job.raw_description) or ""
        subject = f"Application for {role} - {candidate_name}"

        # Resolve body: tailored cover letter or executive pitch
        body: str = ""
        cl_download_url: Optional[str] = None
        if item.cover_letter_doc_id:
            cl_doc = session.exec(
                select(GeneratedDocumentDB).where(GeneratedDocumentDB.doc_id == item.cover_letter_doc_id)
            ).first()
            if cl_doc and cl_doc.content_text:
                body = cl_doc.content_text
                cl_download_url = f"/api/v1/cover-letter/{cl_doc.doc_id}"

        if not body:
            body = (
                f"Dear {company} Hiring Team,\n\n"
                f"I am writing to submit my application for the {role} position. With deep hands-on expertise "
                f"in software engineering and production systems, I have delivered verifiable business and "
                f"technical results across complex architectures.\n\n"
                f"I have attached my tailored ATS CV highlighting specific achievements aligned with {company}'s requirements. "
                f"I would welcome the opportunity to discuss how my technical leadership and execution mindset can contribute "
                f"directly to your team's objectives.\n\n"
                f"Best regards,\n\n"
                f"{candidate_name}\n"
                f"{f'Email: {candidate_email}' if candidate_email else ''}\n"
                f"{f'Phone: {candidate_phone}' if candidate_phone else ''}"
            )

        # Generate URLs
        gmail_web_url = (
            f"https://mail.google.com/mail/?view=cm&fs=1&to={urllib.parse.quote(to_email)}"
            f"&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        )
        mailto_url = (
            f"mailto:{urllib.parse.quote(to_email)}?subject={urllib.parse.quote(subject)}"
            f"&body={urllib.parse.quote(body)}"
        )

        cv_pdf_download_url = (
            f"/api/v1/cv-fit/{item.tailored_cv_doc_id}/download/pdf" if item.tailored_cv_doc_id else None
        )

        return OutreachPackageResponse(
            item_id=item.id,
            job_title=role,
            company_name=company,
            to_email=to_email,
            subject=subject,
            body_markdown=body,
            gmail_web_url=gmail_web_url,
            mailto_url=mailto_url,
            cv_pdf_download_url=cv_pdf_download_url,
            cover_letter_download_url=cl_download_url,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            candidate_phone=candidate_phone,
        )

    def batch_import(
        self, session: Session, request: PipelineBatchImportRequest
    ) -> List[PipelineItemResponse]:
        """
        Migrates pipeline items from client localStorage into the server database.
        """
        imported_ids: List[int] = []
        for raw_item in request.items:
            job_id = raw_item.job_id
            if not job_id and raw_item.job:
                # Find by URL or source_id
                job_url = raw_item.job.get("url")
                job_sid = raw_item.job.get("source_id")
                match_job = None
                if job_url:
                    match_job = session.exec(select(JobDB).where(JobDB.url == job_url)).first()
                if not match_job and job_sid:
                    match_job = session.exec(select(JobDB).where(JobDB.source_id == job_sid)).first()
                if match_job:
                    job_id = match_job.id

            if not job_id:
                continue

            job = session.get(JobDB, job_id)
            if not job or not self.is_eligible(job):
                continue

            try:
                item_in = PipelineItemCreate(
                    job_id=job.id,
                    profile_id=request.profile_id,
                    status=raw_item.status or "saved",
                    recruiter_email=raw_item.recruiter_email,
                    notes=raw_item.notes,
                )
                saved_item = self.add_to_pipeline(session, item_in)
                if raw_item.tailored_cv_doc_id:
                    saved_item.tailored_cv_doc_id = raw_item.tailored_cv_doc_id
                if raw_item.applied_at:
                    saved_item.applied_at = raw_item.applied_at
                session.add(saved_item)
                session.commit()
                imported_ids.append(saved_item.id)
            except Exception:
                continue

        return self.get_pipeline_items(session, profile_id=request.profile_id)


pipeline_service = PipelineService()

