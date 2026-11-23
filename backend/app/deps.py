"""Dépendances FastAPI réutilisables : utilisateur connecté et contrôle des rôles."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ROLE_LEVEL, Membership, Role, User
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    """Lit le token JWT dans l'en-tête Authorization et renvoie l'utilisateur. 401 sinon."""
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentification requise")
    user_id = decode_token(creds.credentials, "access")
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalide ou expiré")
    return user


def get_membership(db: Session, user: User, workspace_id: int, min_role: Role) -> Membership:
    """Vérifie que l'utilisateur est membre de l'espace avec au moins le rôle demandé.

    - Pas membre          -> 404 (on ne révèle même pas que l'espace existe)
    - Membre, rôle faible -> 403
    """
    membership = db.get(Membership, {"user_id": user.id, "workspace_id": workspace_id})
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Espace introuvable")
    if ROLE_LEVEL[membership.role] < ROLE_LEVEL[min_role]:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Rôle '{min_role.value}' requis")
    return membership
