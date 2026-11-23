"""Espaces de travail et gestion des membres.

Règles :
- Tout utilisateur connecté peut créer un espace ; il en devient automatiquement admin.
- Seul un admin de l'espace peut ajouter / modifier / retirer des membres ou supprimer l'espace.
- Un espace doit toujours garder au moins un admin.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_membership
from app.models import Membership, Role, User, Workspace
from app.schemas import MemberIn, MemberOut, RoleIn, WorkspaceIn, WorkspaceOut

router = APIRouter(prefix="/api/workspaces", tags=["Espaces"])


def _out(ws: Workspace, role: Role) -> WorkspaceOut:
    return WorkspaceOut(id=ws.id, name=ws.name, description=ws.description, my_role=role, created_at=ws.created_at)


def _count_admins(db: Session, workspace_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(Membership).where(
            Membership.workspace_id == workspace_id, Membership.role == Role.admin
        )
    )


@router.get("", response_model=list[WorkspaceOut])
def list_my_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Workspace, Membership.role)
        .join(Membership, Membership.workspace_id == Workspace.id)
        .where(Membership.user_id == user.id)
        .order_by(Workspace.name)
    ).all()
    return [_out(ws, role) for ws, role in rows]


@router.post("", response_model=WorkspaceOut, status_code=status.HTTP_201_CREATED)
def create_workspace(data: WorkspaceIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ws = Workspace(name=data.name, description=data.description)
    db.add(ws)
    db.flush()  # pour obtenir ws.id avant le commit
    db.add(Membership(user_id=user.id, workspace_id=ws.id, role=Role.admin))
    db.commit()
    return _out(ws, Role.admin)


@router.get("/{workspace_id}", response_model=WorkspaceOut)
def get_workspace(workspace_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_membership(db, user, workspace_id, Role.viewer)
    return _out(membership.workspace, membership.role)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = get_membership(db, user, workspace_id, Role.admin)
    db.delete(membership.workspace)
    db.commit()


# ---------------- Membres ----------------
@router.get("/{workspace_id}/members", response_model=list[MemberOut])
def list_members(workspace_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    get_membership(db, user, workspace_id, Role.viewer)
    rows = db.execute(
        select(Membership, User).join(User, User.id == Membership.user_id)
        .where(Membership.workspace_id == workspace_id).order_by(User.full_name)
    ).all()
    return [MemberOut(user_id=u.id, email=u.email, full_name=u.full_name, role=m.role) for m, u in rows]


@router.post("/{workspace_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    workspace_id: int, data: MemberIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_membership(db, user, workspace_id, Role.admin)
    new_user = db.scalar(select(User).where(User.email == data.email.lower()))
    if new_user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun compte avec cet email (la personne doit s'inscrire)")
    if db.get(Membership, {"user_id": new_user.id, "workspace_id": workspace_id}):
        raise HTTPException(status.HTTP_409_CONFLICT, "Cette personne est déjà membre")
    db.add(Membership(user_id=new_user.id, workspace_id=workspace_id, role=data.role))
    db.commit()
    return MemberOut(user_id=new_user.id, email=new_user.email, full_name=new_user.full_name, role=data.role)


@router.patch("/{workspace_id}/members/{member_id}", response_model=MemberOut)
def change_role(
    workspace_id: int,
    member_id: int,
    data: RoleIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_membership(db, user, workspace_id, Role.admin)
    target = db.get(Membership, {"user_id": member_id, "workspace_id": workspace_id})
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membre introuvable")
    if target.role == Role.admin and data.role != Role.admin and _count_admins(db, workspace_id) == 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'espace doit garder au moins un admin")
    target.role = data.role
    db.commit()
    return MemberOut(user_id=target.user.id, email=target.user.email, full_name=target.user.full_name, role=target.role)


@router.delete("/{workspace_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    workspace_id: int, member_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    get_membership(db, user, workspace_id, Role.admin)
    target = db.get(Membership, {"user_id": member_id, "workspace_id": workspace_id})
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membre introuvable")
    if target.role == Role.admin and _count_admins(db, workspace_id) == 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "L'espace doit garder au moins un admin")
    db.delete(target)
    db.commit()
