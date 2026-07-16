from fastapi.testclient import TestClient

from tests.conftest import DEFAULT_PASSWORD


def test_get_user_success(seeded_user, auth_token, client: TestClient):
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {auth_token}"}
    )
    data = response.json()

    assert response.status_code == 200
    assert data["email"] == seeded_user.email
    assert "password" not in data


def test_get_user_unauthenticated(client: TestClient):
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401


def test_update_user_success(seeded_user, auth_token, client: TestClient):
    response = client.patch(
        "/api/v1/users/me",
        json={"first_name": "Ella"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["first_name"] == "Ella"
    assert data["last_name"] == seeded_user.last_name


def test_update_user_authenticated(client: TestClient):
    response = client.patch(
        "/api/v1/users/me",
        json={"first_name": "Ella"},
    )
    assert response.status_code == 401


def test_update_password_success(auth_token, client: TestClient):
    response = client.patch(
        "/api/v1/users/me/update-password",
        json={
            "current_password": DEFAULT_PASSWORD,
            "new_password": "qwerty_12345",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["message"] == "Password updated successfully"


def test_update_password_wrong_current(auth_token, client: TestClient):
    response = client.patch(
        "/api/v1/users/me/update-password",
        json={
            "current_password": "changeMe123!",
            "new_password": "qwerty_12345",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    data = response.json()

    assert response.status_code == 400
    assert data["detail"] == "Incorrect password"


def test_update_password_unauthenticated(client: TestClient):
    response = client.patch(
        "/api/v1/users/me/update-password",
        json={
            "current_password": DEFAULT_PASSWORD,
            "new_password": "qwerty_12345",
        },
    )
    assert response.status_code == 401


def test_delete_user_success(auth_token, client: TestClient):
    response = client.delete(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 204


def test_delete_user_unauthenticated(client: TestClient):
    response = client.delete(
        "/api/v1/users/me",
    )
    assert response.status_code == 401
