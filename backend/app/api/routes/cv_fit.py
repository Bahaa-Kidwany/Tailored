import re
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from app.schemas.cv_fit import CvFitCreateRequest, CvFitDetailResponse, CvFitSummaryResponse
from app.ai.tailor.cv_fit_service import cv_fit_service
from app.ai.formatters.latex_engine import _generate_fallback_ats_pdf

router = APIRouter(prefix="/cv-fit", tags=["cv_fit"])


def _safe_filename(company: Optional[str], title: Optional[str], ext: str) -> str:
    c = re.sub(r"[^a-zA-Z0-9]+", "_", (company or "Company").strip()).strip("_")
    t = re.sub(r"[^a-zA-Z0-9]+", "_", (title or "Role").strip()).strip("_")
    return f"Tailored_CV_{c}_{t}.{ext}"


@router.post("", response_model=CvFitDetailResponse)
def create_cv_fit(payload: CvFitCreateRequest) -> CvFitDetailResponse:
    try:
        return cv_fit_service.create_cv_fit(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get("", response_model=List[CvFitSummaryResponse])
def list_cv_fits(profile_id: Optional[int] = Query(default=None)) -> List[CvFitSummaryResponse]:
    return cv_fit_service.list_cv_fits(profile_id=profile_id)


@router.get("/{cv_fit_id}", response_model=CvFitDetailResponse)
def get_cv_fit(cv_fit_id: str) -> CvFitDetailResponse:
    doc = cv_fit_service.get_cv_fit(cv_fit_id)
    if not doc:
        raise HTTPException(status_code=404, detail="CV Fit document not found")
    return doc


@router.get("/{cv_fit_id}/download/{kind}")
def download_artifact(cv_fit_id: str, kind: str):
    if kind not in ("tex", "pdf"):
        raise HTTPException(status_code=400, detail="Unsupported artifact kind. Use 'pdf' or 'tex'.")

    doc = cv_fit_service.get_cv_fit(cv_fit_id)
    if not doc:
        raise HTTPException(status_code=404, detail="CV Fit document not found")

    download_name = _safe_filename(doc.company_name, doc.job_title, kind)
    media = "text/x-tex" if kind == "tex" else "application/pdf"

    for f in doc.files:
        if f.kind == kind and f.artifact_path and Path(f.artifact_path).exists():
            return FileResponse(path=f.artifact_path, media_type=media, filename=download_name)

    # On-demand fallback if PDF was requested for a legacy record with only .tex
    if kind == "pdf":
        tex_file = next((Path(f.artifact_path) for f in doc.files if f.kind == "tex" and f.artifact_path and Path(f.artifact_path).exists()), None)
        if tex_file:
            pdf_file = tex_file.parent / "cv.pdf"
            if _generate_fallback_ats_pdf(tex_file, pdf_file):
                return FileResponse(path=str(pdf_file), media_type="application/pdf", filename=download_name)

    if kind == "tex" and doc.tailored_latex_content:
        return Response(
            content=doc.tailored_latex_content,
            media_type="text/x-tex",
            headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
        )

    raise HTTPException(status_code=404, detail=f"Requested artifact ({kind}) not available")
