# app/main.py
from fastapi import FastAPI
from app.api import reco_router, bizOcr_router

app = FastAPI()

app.include_router(reco_router.router)

# 사업자 등록증 OCR API
app.include_router(bizOcr_router.router)