from tests.conftest import register_and_login


def test_register_login_me(client):
    r = client.post(
        "/api/auth/register", json={"email": "Siham@Test.com", "full_name": "Siham", "password": "motdepasse123"}
    )
    assert r.status_code == 201
    assert r.json()["email"] == "siham@test.com"  # email normalisé en minuscules

    r = client.post("/api/auth/login", json={"email": "siham@test.com", "password": "motdepasse123"})
    assert r.status_code == 200
    tokens = r.json()

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Siham"


def test_duplicate_email_and_wrong_password(client):
    body = {"email": "a@test.com", "full_name": "Amal", "password": "motdepasse123"}
    assert client.post("/api/auth/register", json=body).status_code == 201
    assert client.post("/api/auth/register", json=body).status_code == 409
    r = client.post("/api/auth/login", json={"email": "a@test.com", "password": "mauvais"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/workspaces").status_code == 401
    assert client.get("/api/workspaces", headers={"Authorization": "Bearer faux"}).status_code == 401


def test_refresh_token(client):
    client.post("/api/auth/register", json={"email": "b@test.com", "full_name": "Badr", "password": "motdepasse123"})
    tokens = client.post("/api/auth/login", json={"email": "b@test.com", "password": "motdepasse123"}).json()
    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    # un access token ne peut pas servir de refresh token
    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


def test_short_password_rejected(client):
    r = client.post("/api/auth/register", json={"email": "c@test.com", "full_name": "Chama", "password": "123"})
    assert r.status_code == 422
    assert register_and_login  # import utilisé
