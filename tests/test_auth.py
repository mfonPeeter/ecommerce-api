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
