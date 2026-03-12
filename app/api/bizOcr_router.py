from fastapi import APIRouter, Depends
from app.core.security import require_internal_api_key
from app.schemas.bizOcr_schema import BizOcrRequest, BizOcrResponse
from app.services.bizOcr_service import extract_business_info

router = APIRouter(
    prefix="/biz/signup",
    tags=["Biz Signup OCR"],
    # dependencies=[Depends(require_internal_api_key)]
)


@router.post("/ocr", response_model=BizOcrResponse)
async def business_license_ocr(req: BizOcrRequest):
    """
    사업자등록증 OCR API

    Spring → Base64 이미지 전달
    FastAPI → OCR 분석
    """

    result = extract_business_info(req.imageBase64)

    return result