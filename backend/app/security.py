"""Hachage des mots de passe (bcrypt) et création / lecture des tokens JWT.

Deux types de tokens :
- access token  (30 min)  : envoyé à chaque requête dans l'en-tête "Authorization: Bearer ..."
- refresh token (7 jours) : sert uniquement à obtenir un nouveau access token sans se reconnecter
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def _create_token(user_id: int, token_type: str, expires: timedelta) -> str:
    payload = {
        "sub": str(user_id),  # "subject" = l'utilisateur concerné
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: int) -> str:
    return _create_token(user_id, "access", timedelta(minutes=settings.access_token_minutes))


def create_refresh_token(user_id: int) -> str:
    return _create_token(user_id, "refresh", timedelta(days=settings.refresh_token_days))


def decode_token(token: str, expected_type: str) -> int | None:
    """Renvoie l'id de l'utilisateur si le token est valide et du bon type, sinon None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:  # signature invalide, token expiré, etc.
        return None
    if payload.get("type") != expected_type:
        return None
    return int(payload["sub"])
