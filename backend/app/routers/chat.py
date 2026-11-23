"""Chat RAG avec réponse en streaming (Server-Sent Events).

Déroulement d'une question :
1. Vérifier que l'utilisateur est membre de l'espace (n'importe quel rôle).
2. Rechercher les passages les plus proches dans les documents DE CET ESPACE uniquement.
3. Envoyer d'abord un événement "meta" avec les citations (document + page).
4. Envoyer la réponse du LLM morceau par morceau (événements "token").
5. Enregistrer la question et la réponse dans l'historique, puis envoyer "done".

Format SSE : chaque événement est une ligne "data: {json}" suivie d'une ligne vide.
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.deps import get_current_user, get_membership
from app.models import Conversation, Message, Role, User
from app.rag.llm import stream_answer
from app.rag.retrieval import search
from app.schemas import ChatIn, ConversationOut, MessageOut

router = APIRouter(tags=["Chat"])


def sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/api/workspaces/{workspace_id}/chat")
def chat(workspace_id: int, data: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_membership(db, user, workspace_id, Role.viewer)

    # Conversation existante ou nouvelle
    if data.conversation_id:
        conv = db.get(Conversation, data.conversation_id)
        if conv is None or conv.user_id != user.id or conv.workspace_id != workspace_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")
    else:
        conv = Conversation(user_id=user.id, workspace_id=workspace_id, title=data.question[:80])
        db.add(conv)
        db.flush()
    db.add(Message(conversation_id=conv.id, role="user", content=data.question, citations=[]))
    db.commit()

    chunks = search(db, workspace_id, data.question)
    citations = [
        {"index": i, "document_id": c.document_id, "filename": c.filename, "page": c.page,
         "excerpt": c.content[:200]}
        for i, c in enumerate(chunks, start=1)
    ]
    conversation_id = conv.id

    def event_stream():
        yield sse({"type": "meta", "conversation_id": conversation_id, "citations": citations})
        answer = ""
        try:
            for token in stream_answer(data.question, chunks):
                answer += token
                yield sse({"type": "token", "text": token})
        except Exception as exc:  # ex. clé d'API invalide, quota dépassé
            yield sse({"type": "error", "message": f"Erreur du LLM : {exc}"})
            answer += "\n[Réponse interrompue]"
        # Nouvelle session : celle de la requête peut déjà être fermée pendant le streaming
        with SessionLocal() as s:
            s.add(Message(conversation_id=conversation_id, role="assistant", content=answer, citations=citations))
            s.commit()
        yield sse({"type": "done"})

    return StreamingResponse(event_stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/api/workspaces/{workspace_id}/conversations", response_model=list[ConversationOut])
def list_conversations(workspace_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_membership(db, user, workspace_id, Role.viewer)
    return db.scalars(
        select(Conversation)
        .where(Conversation.workspace_id == workspace_id, Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
    ).all()


@router.get("/api/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def list_messages(conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Conversation introuvable")
    get_membership(db, user, conv.workspace_id, Role.viewer)  # toujours membre de l'espace ?
    return conv.messages
