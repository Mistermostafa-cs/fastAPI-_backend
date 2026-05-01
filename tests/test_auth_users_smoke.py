from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_success() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@school.com", "password": "Admin@123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert "access_token" in data


def test_login_fail() -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "admin@school.com", "password": "wrong"},
    )
    assert response.status_code == 401


def test_auth_me_and_users() -> None:
    login = client.post(
        "/api/auth/login",
        json={"email": "admin@school.com", "password": "Admin@123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/api/auth/me", headers=headers)
    assert me_response.status_code == 200

    users_response = client.get("/api/users", headers=headers)
    assert users_response.status_code == 200

    roles_response = client.get("/api/roles", headers=headers)
    assert roles_response.status_code == 200

    academic_years_response = client.get("/api/academics/academic-years", headers=headers)
    assert academic_years_response.status_code == 200
