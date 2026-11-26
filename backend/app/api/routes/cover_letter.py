from typing import List
from fastapi import APIRouter, HTTPException
from app.schemas.cv_fit import CoverLetterCreateRequest, CoverLetterResponse
from app.ai.cover_letter.cover_letter_service import cover_letter_service

router = APIRouter(prefix="/cover-letter", tags=["cover_letter"])

@router.post("", response_model=CoverLetterResponse)
def generate_cover_letter(payload: CoverLetterCreateRequest) -> CoverLetterResponse:
    try:
        return cover_letter_service.generate_cover_letter(payload)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@router.get("", response_model=List[CoverLetterResponse])
def list_cover_letters() -> List[CoverLetterResponse]:
    return cover_letter_service.list_cover_letters()
