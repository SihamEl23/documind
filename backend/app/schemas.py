"""Schémas Pydantic : la forme des données qui entrent et sortent de l'API."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import DocumentStatus, Role


# ---------- Auth ----------
class RegisterIn(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokensOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str


# ---------- Espaces ----------
class WorkspaceIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = ""


class WorkspaceOut(BaseModel):
    id: int
    name: str
    description: str
    my_role: Role
    created_at: datetime


class MemberIn(BaseModel):
    email: EmailStr
    role: Role = Role.viewer


class RoleIn(BaseModel):
    role: Role


class MemberOut(BaseModel):
    user_id: int
    email: EmailStr
    full_name: str
    role: Role


# ---------- Documents ----------
class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    workspace_id: int
    filename: str
    status: DocumentStatus
    pages: int
    error_message: str
    created_at: datetime


# ---------- Chat ----------
class ChatIn(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    conversation_id: int | None = None


class Citation(BaseModel):
    index: int
    document_id: int
    filename: str
    page: int
    excerpt: str


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    citations: list[Citation]
    created_at: datetime
