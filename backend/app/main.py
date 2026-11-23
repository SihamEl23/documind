"""Point d'entrée de l'API. Lancer avec : uvicorn app.main:app --reload"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import auth, chat, documents, workspaces

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # crée l'extension pgvector et les tables au démarrage
    yield


app = FastAPI(
    title="DocuMind API",
    description="Assistant IA de questions-réponses sur documents (RAG)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["Santé"])
def health():
    return {"status": "ok"}
