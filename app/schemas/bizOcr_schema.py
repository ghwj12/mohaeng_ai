from pydantic import BaseModel

# OCR 요청
class BizOcrRequest(BaseModel):
    imageBase64: str


# OCR 응답
class BizOcrResponse(BaseModel):
    businessNumber: str
    ownerName: str
    openDate: str