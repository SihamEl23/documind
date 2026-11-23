"""Configuration des tests : base PostgreSQL de test, embeddings et LLM simulés (aucune clé nécessaire)."""

import os
import tempfile

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/documind_test")
os.environ["EMBEDDING_PROVIDER"] = "fake"
os.environ["LLM_PROVIDER"] = "fake"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()

import pymupdf  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine, init_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_db():
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_pdf(pages: list[str]) -> bytes:
    """Crée un PDF en mémoire avec une page par texte."""
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


def register_and_login(client, email: str, name: str = "Test User") -> dict:
    client.post("/api/auth/register", json={"email": email, "full_name": name, "password": "motdepasse123"})
    tokens = client.post("/api/auth/login", json={"email": email, "password": "motdepasse123"}).json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}
