import base64
import re
import cv2
import numpy as np
from paddleocr import PaddleOCR
from app.schemas.bizOcr_schema import BizOcrResponse

# OCR 초기화
ocr = PaddleOCR(
    lang="korean",
    use_angle_cls=True
)

def preprocess_image(img):
    # 흑백 전환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # 노이즈 제거
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    # 이진화 (이미지 상태에 따라 효과가 다를 수 있음)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    return thresh

def parse_text(lines):
    business_number = ""
    owner_name = ""
    open_date = ""

    # 1. 모든 라인을 합치되, 공백을 제거하여 텍스트 뭉침 현상에 대응
    full_text = "".join(lines).replace(" ", "")
    
    # [사업자등록번호] 000-00-00000 패턴
    biz_num_match = re.search(r"(\d{3}-\d{2}-\d{5})", full_text)
    if biz_num_match:
        business_number = biz_num_match.group(1)

    # [대표자 성명] 
    # 패턴 설명: '대표자' 또는 '성명' 뒤에 한글이 아닌 문자(특수문자, '다', '자' 등)가 0~5개 올 수 있고, 
    # 그 뒤에 실제 이름(한글 2~4자)이 오는 구조를 찾습니다.
    # 특히 '자' 뒤에 바로 이름이 붙는 '자정호규' 케이스를 위해 '자'를 매칭 그룹에서 제외합니다.
    name_match = re.search(r"(?:대표자|성명)[^가-힣]*[다자]?([가-힣]{2,4})", full_text)
    if name_match:
        owner_name = name_match.group(1)
    
    # [개업연월일]
    # 숫자들만 뽑아서 YYYYMMDD 형식으로 만듭니다.
    # '개업' 단어 근처의 숫자들을 탐색
    date_match = re.search(r"개업[^0-9]*(\d{4})[^0-9]*(\d{1,2})[^0-9]*(\d{1,2})", full_text)
    if date_match:
        year = date_match.group(1)
        month = date_match.group(2).zfill(2)
        day = date_match.group(3).zfill(2)
        open_date = f"{year}{month}{day}"
    else:
        # '개업' 단어가 멀리 있을 경우를 대비한 일반 날짜 패턴
        date_alt_match = re.search(r"(\d{4})년(\d{1,2})월(\d{1,2})일", full_text)
        if date_alt_match:
            open_date = date_alt_match.group(1) + date_alt_match.group(2).zfill(2) + date_alt_match.group(3).zfill(2)

    return business_number, owner_name, open_date

def extract_business_info(imageBase64: str) -> BizOcrResponse:
    try:
        if "," in imageBase64:
            imageBase64 = imageBase64.split(",")[1]

        image_bytes = base64.b64decode(imageBase64)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("이미지 디코딩 실패")

        # 전처리
        processed_img = preprocess_image(img)
        
        # OCR 실행
        result = ocr.ocr(processed_img)

        lines = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                score = line[1][1]
                if score > 0.5: # 신뢰도 0.5 이상만 사용
                    lines.append(text)

        print("OCR 결과 리스트:", lines)

        business_number, owner_name, open_date = parse_text(lines)

        return BizOcrResponse(
            businessNumber=business_number,
            ownerName=owner_name,
            openDate=open_date
        )

    except Exception as e:
        print(f"OCR 처리 중 에러 발생: {e}")
        return BizOcrResponse(businessNumber="", ownerName="", openDate="")