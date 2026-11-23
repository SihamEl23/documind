"""Connexion à PostgreSQL avec SQLAlchemy."""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Active pgvector puis crée les tables si elles n'existent pas encore."""
    from app import models  # noqa: F401  (enregistre les modèles dans Base.metadata)

    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dépendance FastAPI : ouvre une session par requête et la ferme à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
