"""Vérifie les règles d'accès : admin / editor / viewer / non-membre."""

from tests.conftest import make_pdf, register_and_login


def setup_workspace(client):
    admin = register_and_login(client, "admin@test.com", "Admin")
    editor = register_and_login(client, "editor@test.com", "Editor")
    viewer = register_and_login(client, "viewer@test.com", "Viewer")
    outsider = register_and_login(client, "outsider@test.com", "Outsider")
    ws = client.post("/api/workspaces", json={"name": "RH"}, headers=admin).json()
    assert ws["my_role"] == "admin"
    client.post(
        f"/api/workspaces/{ws['id']}/members", json={"email": "editor@test.com", "role": "editor"}, headers=admin
    )
    client.post(
        f"/api/workspaces/{ws['id']}/members", json={"email": "viewer@test.com", "role": "viewer"}, headers=admin
    )
    return ws["id"], admin, editor, viewer, outsider


def upload(client, ws_id, headers, text="Contenu de test"):
    return client.post(
        f"/api/workspaces/{ws_id}/documents",
        files={"file": ("doc.pdf", make_pdf([text]), "application/pdf")},
        headers=headers,
    )


def test_outsider_cannot_see_workspace(client):
    ws_id, *_, outsider = setup_workspace(client)
    assert client.get(f"/api/workspaces/{ws_id}", headers=outsider).status_code == 404
    assert client.get(f"/api/workspaces/{ws_id}/documents", headers=outsider).status_code == 404
    r = client.post(f"/api/workspaces/{ws_id}/chat", json={"question": "Bonjour ?"}, headers=outsider)
    assert r.status_code == 404


def test_viewer_cannot_upload_but_editor_can(client):
    ws_id, admin, editor, viewer, _ = setup_workspace(client)
    assert upload(client, ws_id, viewer).status_code == 403
    assert upload(client, ws_id, editor).status_code == 202
    assert len(client.get(f"/api/workspaces/{ws_id}/documents", headers=viewer).json()) == 1


def test_only_admin_manages_members(client):
    ws_id, admin, editor, viewer, _ = setup_workspace(client)
    r = client.post(f"/api/workspaces/{ws_id}/members", json={"email": "outsider@test.com"}, headers=editor)
    assert r.status_code == 403
    r = client.post(f"/api/workspaces/{ws_id}/members", json={"email": "outsider@test.com"}, headers=admin)
    assert r.status_code == 201
    assert len(client.get(f"/api/workspaces/{ws_id}/members", headers=viewer).json()) == 4


def test_last_admin_cannot_be_removed(client):
    ws_id, admin, *_ = setup_workspace(client)
    me = client.get("/api/auth/me", headers=admin).json()
    r = client.patch(f"/api/workspaces/{ws_id}/members/{me['id']}", json={"role": "viewer"}, headers=admin)
    assert r.status_code == 400
    assert client.delete(f"/api/workspaces/{ws_id}/members/{me['id']}", headers=admin).status_code == 400


def test_non_pdf_rejected(client):
    ws_id, admin, *_ = setup_workspace(client)
    r = client.post(
        f"/api/workspaces/{ws_id}/documents",
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=admin,
    )
    assert r.status_code == 400
