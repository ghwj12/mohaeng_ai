from fastapi import FastAPI
from app.api import reco_router
from app.api.chat_router import router as chat_router

app = FastAPI(title="MOHAENG AI")

app.include_router(reco_router.router)
app.include_router(chat_router)