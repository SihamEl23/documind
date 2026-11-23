"""Inscription, connexion, rafraîchissement du token, profil."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import LoginIn, RefreshIn, RegisterIn, TokensOut, UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["Authentification"])


def _tokens(user_id: int) -> TokensOut:
    return TokensOut(access_token=create_access_token(user_id), refresh_token=create_refresh_token(user_id))


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cet email est déjà utilisé")
    user = User(email=email, full_name=data.full_name, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return user


@router.post("/login", response_model=TokensOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    # Même message d'erreur dans les deux cas : on ne révèle pas si l'email existe
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou mot de passe incorrect")
    return _tokens(user.id)


@router.post("/refresh", response_model=TokensOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    user_id = decode_token(data.refresh_token, "refresh")
    if user_id is None or db.get(User, user_id) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token invalide ou expiré")
    return _tokens(user_id)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
