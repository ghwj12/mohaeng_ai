# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import reco_router
from app.api import image_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 로컬 테스트용이므로 전부 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reco_router.router)
app.include_router(image_router.router)