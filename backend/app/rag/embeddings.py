"""Embeddings : transformer un texte en vecteur de nombres qui représente son sens.

Deux phrases de même sens (même dans deux langues différentes) donnent des vecteurs proches.
- "local" : modèle sentence-transformers multilingue (français, arabe, anglais), gratuit, tourne sur CPU.
            Il est téléchargé automatiquement au premier lancement (~470 Mo).
- "fake"  : vecteur calculé à partir des mots (hashing). Sert pour les tests, sans téléchargement.
"""
import hashlib
import math
import re
from functools import lru_cache

from app.config import settings


class FakeEmbedder:
    """Embedder simple et déterministe : chaque mot active une case du vecteur."""

    def __init__(self, dim: int):
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vec = [0.0] * self.dim
            for word in re.findall(r"\w+", text.lower()):
                idx = int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim
                vec[idx] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            vectors.append([v / norm for v in vec])
        return vectors


class LocalEmbedder:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer  # import lourd, fait seulement si utilisé

        self.model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()


@lru_cache
def get_embedder():
    """Le modèle est chargé une seule fois, au premier appel, puis réutilisé."""
    if settings.embedding_provider == "fake":
        return FakeEmbedder(settings.embedding_dim)
    return LocalEmbedder(settings.embedding_model)
