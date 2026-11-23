"""Ingestion d'un PDF : extraction du texte page par page -> découpage -> embeddings -> PostgreSQL.

Cette fonction tourne en arrière-plan (BackgroundTasks de FastAPI) : l'utilisateur reçoit
une réponse immédiate pendant que le document passe de "pending" à "processing" puis "ready".
"""
import logging

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings
from app.database import SessionLocal
from app.models import Chunk, Document, DocumentStatus
from app.rag.embeddings import get_embedder

logger = logging.getLogger(__name__)


def extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """Renvoie [(numéro_de_page, texte), ...]. Les pages commencent à 1."""
    pages = []
    with pymupdf.open(pdf_path) as pdf:
        for i, page in enumerate(pdf, start=1):
            text = page.get_text().strip()
            if text:
                pages.append((i, text))
    return pages


def split_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Découpe chaque page en morceaux (~800 caractères) en gardant le numéro de page.

    Le chevauchement (overlap) évite de couper une idée en deux entre deux morceaux.
    On découpe page par page pour toujours savoir de quelle page vient un morceau (citations).
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    chunks = []
    for page_number, text in pages:
        for piece in splitter.split_text(text):
            chunks.append((page_number, piece))
    return chunks


def ingest_document(document_id: int) -> None:
    db = SessionLocal()  # session propre à la tâche de fond
    try:
        doc = db.get(Document, document_id)
        if doc is None:
            return
        doc.status = DocumentStatus.processing
        db.commit()

        pages = extract_pages(doc.stored_path)
        if not pages:
            raise ValueError("Aucun texte trouvé (PDF scanné ? un OCR serait nécessaire)")

        pieces = split_pages(pages)
        vectors = get_embedder().embed([text for _, text in pieces])

        db.add_all(
            Chunk(
                document_id=doc.id,
                workspace_id=doc.workspace_id,
                page=page,
                content=text,
                embedding=vector,
            )
            for (page, text), vector in zip(pieces, vectors)
        )
        doc.pages = max(p for p, _ in pages)
        doc.status = DocumentStatus.ready
        db.commit()
        logger.info("Document %s indexé : %s morceaux", doc.id, len(pieces))
    except Exception as exc:  # on enregistre l'erreur pour l'afficher dans l'interface
        db.rollback()
        doc = db.get(Document, document_id)
        if doc is not None:
            doc.status = DocumentStatus.error
            doc.error_message = str(exc)[:500]
            db.commit()
        logger.exception("Échec de l'indexation du document %s", document_id)
    finally:
        db.close()
