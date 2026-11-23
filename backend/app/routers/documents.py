"""Upload, liste, téléchargement et suppression des documents d'un espace.

- Lister / ouvrir un document : tout membre (viewer, editor, admin)
- Ajouter / supprimer un document : editor ou admin
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, get_membership
from app.models import Document, Role, User
from app.rag.ingestion import ingest_document
from app.schemas import DocumentOut

router = APIRouter(tags=["Documents"])


@router.get("/api/workspaces/{workspace_id}/documents", response_model=list[DocumentOut])
def list_documents(workspace_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_membership(db, user, workspace_id, Role.viewer)
    return db.scalars(
        select(Document).where(Document.workspace_id == workspace_id).order_by(Document.created_at.desc())
    ).all()


@router.post(
    "/api/workspaces/{workspace_id}/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_202_ACCEPTED,  # 202 = "reçu, traitement en cours"
)
async def upload_document(
    workspace_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_membership(db, user, workspace_id, Role.editor)

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Seuls les fichiers PDF sont acceptés")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Fichier > {settings.max_upload_mb} Mo")
    if not content.startswith(b"%PDF"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le fichier n'est pas un PDF valide")

    folder = Path(settings.upload_dir) / str(workspace_id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / f"{uuid.uuid4().hex}.pdf"  # nom unique : évite les collisions et les noms dangereux
    stored_path.write_bytes(content)

    doc = Document(
        workspace_id=workspace_id,
        filename=os.path.basename(file.filename),
        stored_path=str(stored_path),
        uploaded_by=user.id,
    )
    db.add(doc)
    db.commit()

    # L'indexation (extraction + embeddings) se fait après l'envoi de la réponse
    background_tasks.add_task(ingest_document, doc.id)
    return doc


def _get_doc_for_user(db: Session, user: User, document_id: int, min_role: Role) -> Document:
    doc = db.get(Document, document_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document introuvable")
    get_membership(db, user, doc.workspace_id, min_role)
    return doc


@router.get("/api/documents/{document_id}/file")
def download_document(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _get_doc_for_user(db, user, document_id, Role.viewer)
    return FileResponse(doc.stored_path, media_type="application/pdf", filename=doc.filename,
                        content_disposition_type="inline")


@router.delete("/api/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = _get_doc_for_user(db, user, document_id, Role.editor)
    path = Path(doc.stored_path)
    db.delete(doc)  # supprime aussi ses chunks (cascade)
    db.commit()
    path.unlink(missing_ok=True)
