"""Appel du LLM avec les passages retrouvés (la partie "Generation" de RAG).

Le LLM reçoit une consigne stricte : répondre uniquement à partir des passages fournis,
et citer ses sources avec [1], [2]... Les réponses sont générées en streaming (morceau par morceau).
"""
from collections.abc import Iterator

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.rag.retrieval import RetrievedChunk

SYSTEM_PROMPT = """Tu es DocuMind, un assistant qui répond aux questions à partir des documents d'une organisation.
Règles :
1. Réponds UNIQUEMENT avec les informations des passages fournis. N'invente rien.
2. Cite tes sources avec leur numéro entre crochets, par exemple [1] ou [2][3].
3. Si les passages ne contiennent pas la réponse, dis-le clairement.
4. Réponds dans la langue de la question (français, arabe ou anglais).
5. Sois clair et concis."""


def build_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, c in enumerate(chunks, start=1):
        parts.append(f"[{i}] Document : {c.filename} (page {c.page})\n{c.content}")
    return "\n\n".join(parts)


def build_messages(question: str, chunks: list[RetrievedChunk]):
    user_prompt = f"Passages :\n\n{build_context(chunks)}\n\nQuestion : {question}"
    return [SystemMessage(SYSTEM_PROMPT), HumanMessage(user_prompt)]


def _get_chat_model():
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0.1)
    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.gemini_model, google_api_key=settings.google_api_key, temperature=0.1
        )
    raise ValueError(f"LLM_PROVIDER inconnu : {settings.llm_provider}")


def _fake_stream(chunks: list[RetrievedChunk]) -> Iterator[str]:
    """Réponse simulée, pour les tests et pour essayer l'app sans clé d'API."""
    if not chunks:
        text = "Je n'ai trouvé aucune information sur ce sujet dans les documents."
    else:
        text = f"D'après les documents : {chunks[0].content[:300]} [1]"
    for word in text.split(" "):
        yield word + " "


def stream_answer(question: str, chunks: list[RetrievedChunk]) -> Iterator[str]:
    if settings.llm_provider == "fake":
        yield from _fake_stream(chunks)
        return
    if not chunks:
        yield "Je n'ai trouvé aucun document pertinent dans cet espace pour répondre à cette question."
        return
    for part in _get_chat_model().stream(build_messages(question, chunks)):
        if part.content:
            yield part.content if isinstance(part.content, str) else str(part.content)
