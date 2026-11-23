"""Teste le pipeline complet : upload -> indexation -> question -> réponse streamée avec citations."""

import json

from tests.conftest import make_pdf, register_and_login


def read_sse(response) -> list[dict]:
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


def test_upload_is_indexed(client):
    h = register_and_login(client, "a@test.com")
    ws = client.post("/api/workspaces", json={"name": "RH"}, headers=h).json()
    pdf = make_pdf(
        ["Page un : horaires de travail.", "Page deux : le télétravail est autorisé deux jours par semaine."]
    )
    r = client.post(
        f"/api/workspaces/{ws['id']}/documents", files={"file": ("reglement.pdf", pdf, "application/pdf")}, headers=h
    )
    assert r.status_code == 202
    assert r.json()["status"] == "pending"

    # Le TestClient exécute la tâche de fond juste après la réponse
    docs = client.get(f"/api/workspaces/{ws['id']}/documents", headers=h).json()
    assert docs[0]["status"] == "ready"
    assert docs[0]["pages"] == 2


def test_chat_streams_answer_with_page_citation(client):
    h = register_and_login(client, "a@test.com")
    ws = client.post("/api/workspaces", json={"name": "RH"}, headers=h).json()
    pdf = make_pdf(["Les horaires sont de 9h à 18h.", "Le télétravail est autorisé deux jours par semaine."])
    client.post(
        f"/api/workspaces/{ws['id']}/documents", files={"file": ("reglement.pdf", pdf, "application/pdf")}, headers=h
    )

    r = client.post(
        f"/api/workspaces/{ws['id']}/chat",
        json={"question": "Combien de jours de télétravail par semaine ?"},
        headers=h,
    )
    assert r.status_code == 200
    events = read_sse(r)

    meta = events[0]
    assert meta["type"] == "meta"
    assert meta["citations"][0]["filename"] == "reglement.pdf"
    assert meta["citations"][0]["page"] == 2  # le passage le plus pertinent est en page 2

    tokens = [e for e in events if e["type"] == "token"]
    assert len(tokens) > 1  # la réponse arrive en plusieurs morceaux (streaming)
    assert events[-1]["type"] == "done"

    # La conversation est enregistrée dans l'historique
    convs = client.get(f"/api/workspaces/{ws['id']}/conversations", headers=h).json()
    msgs = client.get(f"/api/conversations/{convs[0]['id']}/messages", headers=h).json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert msgs[1]["citations"][0]["page"] == 2


def test_search_never_crosses_workspaces(client):
    h = register_and_login(client, "a@test.com")
    rh = client.post("/api/workspaces", json={"name": "RH"}, headers=h).json()
    finance = client.post("/api/workspaces", json={"name": "Finance"}, headers=h).json()
    client.post(
        f"/api/workspaces/{rh['id']}/documents",
        files={"file": ("salaires.pdf", make_pdf(["Grille des salaires confidentielle."]), "application/pdf")},
        headers=h,
    )

    r = client.post(
        f"/api/workspaces/{finance['id']}/chat", json={"question": "Quelle est la grille des salaires ?"}, headers=h
    )
    meta = read_sse(r)[0]
    assert meta["citations"] == []  # l'espace Finance ne voit pas les documents RH
