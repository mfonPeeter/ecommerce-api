from fastapi.testclient import TestClient

from .conftest import DEFAULT_PASSWORD


def test_register_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "Tester",
            "phone_no": "08123348329",
            "password": DEFAULT_PASSWORD,
            "role": "customer",
        },
    )
    data = response.json()

    assert response.status_code == 201
    assert data["access_token"] is not None
    assert data["user"]["email"] == "test@test.com"
    assert "password" not in data["user"]


def test_register_existing_email(seeded_user, client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": seeded_user.email,
            "first_name": seeded_user.first_name,
            "last_name": seeded_user.last_name,
            "phone_no": seeded_user.phone_no,
            "password": DEFAULT_PASSWORD,
            "role": seeded_user.role,
        },
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "User already exists"}


def test_register_success_without_phone(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test2@test.com",
            "first_name": "Test",
            "last_name": "Tester",
            "password": DEFAULT_PASSWORD,
            "role": "customer",
        },
    )
    data = response.json()

    assert response.status_code == 201
    assert data["user"]["phone_no"] is None


def test_login_success(seeded_user, client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": seeded_user.email, "password": DEFAULT_PASSWORD},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["access_token"] is not None
    assert data["user"]["email"] == seeded_user.email
    assert "password" not in data["user"]


def test_login_wrong_password(seeded_user, client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": seeded_user.email, "password": "wrong_password1234"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_login_email_not_found(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@test.com", "password": DEFAULT_PASSWORD},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_phone_no_short(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "Tester",
            "phone_no": "081",
            "password": DEFAULT_PASSWORD,
            "role": "customer",
        },
    )
    assert response.status_code == 422


def test_phone_no_long(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "Tester",
            "phone_no": "08132457973927232332423",
            "password": DEFAULT_PASSWORD,
            "role": "customer",
        },
    )
    assert response.status_code == 422


def test_password_short(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "first_name": "Test",
            "last_name": "Tester",
            "phone_no": "08132457313",
            "password": "qwerty",
            "role": "customer",
        },
    )
    assert response.status_code == 422
