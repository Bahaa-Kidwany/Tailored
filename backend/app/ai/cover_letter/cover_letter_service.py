from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from sqlmodel import Session, select
from app.core.config import settings
from app.core.database import engine
from app.models.job import JobDB
from app.models.document import GeneratedDocumentDB
import app.models.profile  # noqa: F401
from app.schemas.cv_fit import CoverLetterCreateRequest, CoverLetterResponse
from app.scrapers.crawler import company_crawler
from app.ai.providers.base import BaseLLMProvider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.mock_provider import MockLLMProvider

class CoverLetterService:
    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        if llm_provider is not None:
            self.llm = llm_provider
        elif settings.ai_provider == "mock":
            self.llm = MockLLMProvider()
        else:
            try:
                self.llm = GeminiProvider()
            except Exception:
                self.llm = MockLLMProvider()

    def generate_cover_letter(self, request: CoverLetterCreateRequest) -> CoverLetterResponse:
        doc_id = str(uuid4())

        # 1. Resolve job details from database if job_id provided
        if request.job_id:
            with Session(engine) as session:
                job_record = session.get(JobDB, request.job_id)
                if job_record:
                    request.job_title = request.job_title or job_record.title
                    request.company_name = request.company_name or job_record.company_name
                    request.job_description_text = request.job_description_text or job_record.raw_description

        # 2. Crawl company background if URL provided
        crawl_summary = company_crawler.crawl_company_context(request.company_website_url)
        
        system_prompt = (
            "You are an expert career strategist and executive coach. "
            "Write a highly compelling, authentic, tailored cover letter. "
            "Never invent facts, metrics, or degrees not in the candidate's CV."
        )
        
        user_prompt = (
            f"Target Company: {request.company_name or 'Hiring Team'}\n"
            f"Target Role: {request.job_title or 'Target Role'}\n"
            f"Tone: {request.tone}\n\n"
            f"Job Description:\n{request.job_description_text or ''}\n\n"
            f"Company Context:\n{crawl_summary.get('summary_text', '')}\n\n"
            f"Candidate Base Profile / CV:\n{request.base_cv_text}\n\n"
            "Format the response with a professional Subject Line and Markdown Body."
        )
        
        content = self.llm.generate(system_prompt=system_prompt, user_text=user_prompt)
        
        company = request.company_name or "Hiring Team"
        role = request.job_title or "Target Role"
        subject_line = f"Application for {role} - {company}"
        now = datetime.now(timezone.utc)

        # 3. Persist generated cover letter into database
        db_record = GeneratedDocumentDB(
            doc_id=doc_id,
            doc_type="cover_letter",
            job_id=request.job_id,
            job_title=role,
            company_name=company,
            company_website_url=request.company_website_url,
            job_description_text=request.job_description_text,
            status="completed",
            content_text=content,
            created_at=now,
            updated_at=now,
        )

        with Session(engine) as session:
            session.add(db_record)
            session.commit()
            session.refresh(db_record)

        return CoverLetterResponse(
            doc_id=doc_id,
            job_id=request.job_id,
            subject_line=subject_line,
            body_markdown=content,
            company_name=company,
            job_title=role,
            created_at=now,
        )

    def list_cover_letters(self) -> List[CoverLetterResponse]:
        with Session(engine) as session:
            rows = session.exec(
                select(GeneratedDocumentDB)
                .where(GeneratedDocumentDB.doc_type == "cover_letter")
                .order_by(GeneratedDocumentDB.created_at.desc())
            ).all()
            return [
                CoverLetterResponse(
                    doc_id=r.doc_id,
                    job_id=r.job_id,
                    subject_line=f"Application for {r.job_title} - {r.company_name}",
                    body_markdown=r.content_text or "",
                    company_name=r.company_name,
                    job_title=r.job_title,
                    created_at=r.created_at,
                )
                for r in rows
            ]

cover_letter_service = CoverLetterService()
