import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.categories.models import Category


def test_get_categories_success(session: Session, client: TestClient):
    category_1 = Category(
        name="Electronics",
        description="This is a category belonging to just electronics",
    )
    category_2 = Category(
        name="Cars",
        description="This is a category belonging to just cars",
    )
    session.add(category_1)
    session.add(category_2)
    session.commit()

    response = client.get("/api/v1/category")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["name"] == "Electronics"
    assert data[1]["name"] == "Cars"


def test_get_categories_with_search(session: Session, client: TestClient):
    category_1 = Category(
        name="Electronics",
        description="Electronics description",
    )
    category_2 = Category(
        name="Cars",
        description="Cars description",
    )
    session.add(category_1)
    session.add(category_2)
    session.commit()

    response = client.get("/api/v1/category?search=car")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["name"] == "Cars"


def test_create_category_success(vendor_auth_token, client: TestClient):
    response = client.post(
        "/api/v1/category",
        json={"name": "Electronics", "description": "Electronics description"},
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 201
    assert data["name"] == "Electronics"


def test_create_existing_category(
    seeded_category, vendor_auth_token, client: TestClient
):
    response = client.post(
        "/api/v1/category",
        json={"name": seeded_category.name, "description": "Electronics description"},
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"] == "Category already exists"


def test_create_category_unauthenticated(client: TestClient):
    response = client.post(
        "/api/v1/category",
        json={"name": "Electronics", "description": "Electronics description"},
    )

    assert response.status_code == 401


def test_update_category_success(
    vendor_auth_token, seeded_category, client: TestClient
):
    response = client.patch(
        f"/api/v1/category/{seeded_category.id}",
        json={"name": "Electronics"},
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == "Electronics"


def test_update_category_not_found(vendor_auth_token, client: TestClient):
    response = client.patch(
        f"/api/v1/category/{uuid.uuid4()}",
        json={"name": "Electronics"},
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Category does not exist"


def test_update_category_existing_name(
    vendor_auth_token, client: TestClient, session: Session
):
    category_1 = Category(
        name="Electronics",
        description="This is a category belonging to just electronics",
    )
    category_2 = Category(
        name="Cars",
        description="This is a category belonging to just cars",
    )
    session.add(category_1)
    session.add(category_2)
    session.commit()

    response = client.patch(
        f"/api/v1/category/{category_1.id}",
        json={"name": "Cars"},
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 409
    assert data["detail"] == "Category already exists"


def test_update_category_same_name(
    vendor_auth_token, seeded_category, client: TestClient
):
    response = client.patch(
        f"/api/v1/category/{seeded_category.id}",
        json={"name": seeded_category.name, "description": "Changing the description"},
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 200
    assert data["name"] == seeded_category.name
    assert data["description"] == "Changing the description"


def test_update_category_unauthenticated(client: TestClient):
    response = client.patch(
        f"/api/v1/category/{uuid.uuid4()}",
        json={"name": "Electronics"},
    )

    assert response.status_code == 401


def test_delete_category_success(
    vendor_auth_token, seeded_category, client: TestClient
):
    response = client.delete(
        f"/api/v1/category/{seeded_category.id}",
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )

    assert response.status_code == 204


def test_update_delete_not_found(vendor_auth_token, client: TestClient):
    response = client.delete(
        f"/api/v1/category/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {vendor_auth_token}"},
    )
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == "Category does not exist"


def test_update_delete_unauthenticated(client: TestClient):
    response = client.delete(
        f"/api/v1/category/{uuid.uuid4()}",
    )

    assert response.status_code == 401
