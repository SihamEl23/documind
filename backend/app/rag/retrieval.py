"""Recherche sémantique : trouver les morceaux de documents les plus proches de la question.

La question est transformée en vecteur, puis PostgreSQL (pgvector) trie les morceaux
par distance cosinus. Le filtre sur workspace_id garantit qu'un utilisateur ne reçoit
jamais de passages venant d'un espace dont il n'est pas membre.
"""
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Chunk, Document, DocumentStatus
from app.rag.embeddings import get_embedder


@dataclass
class RetrievedChunk:
    document_id: int
    filename: str
    page: int
    content: str
    distance: float


def search(db: Session, workspace_id: int, question: str, k: int | None = None) -> list[RetrievedChunk]:
    query_vector = get_embedder().embed([question])[0]
    distance = Chunk.embedding.cosine_distance(query_vector).label("distance")

    stmt = (
        select(Chunk, Document.filename, distance)
        .join(Document, Document.id == Chunk.document_id)
        .where(Chunk.workspace_id == workspace_id, Document.status == DocumentStatus.ready)
        .order_by(distance)
        .limit(k or settings.top_k)
    )
    return [
        RetrievedChunk(
            document_id=chunk.document_id,
            filename=filename,
            page=chunk.page,
            content=chunk.content,
            distance=float(dist),
        )
        for chunk, filename, dist in db.execute(stmt).all()
    ]
