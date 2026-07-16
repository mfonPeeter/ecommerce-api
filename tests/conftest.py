# Import all models so SQLModel.metadata knows about all tables for tests
import app.db.models

import pytest

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlmodel import Session, create_engine, SQLModel
from fastapi.testclient import TestClient

from main import app
from app.config import settings
from app.database import get_session
from app.users.models import User
from app.auth.utils import get_password_hash

DEFAULT_PASSWORD = "qwertyasdf"


@pytest.fixture(scope="session", autouse=True)
def migrate_database():
    """
    Apply Alembic migrations once before running tests.
    """
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", settings.test_database_url)
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def engine():
    return create_engine(settings.test_database_url)


@pytest.fixture()
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def clean_database(session: Session):
    """
    Reset database state after each test so tests remain isolated.
    """
    yield
    table_names = ", ".join(
        f'"{table.name}"' for table in SQLModel.metadata.sorted_tables
    )
    session.exec(text(f"""
            TRUNCATE TABLE {table_names}
            RESTART IDENTITY CASCADE
            """))
    session.commit()


@pytest.fixture()
def client(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_user(session: Session) -> User:
    """Creates a test user in the database. Returns the user object for tests that need it."""
    user = User(
        email="test@test.com",
        first_name="Test",
        last_name="Tester",
        phone_no="0812273822",
        password=get_password_hash(DEFAULT_PASSWORD),
        role="customer",
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@pytest.fixture
def auth_token(seeded_user, client: TestClient) -> str:
    """Logs in the seeded user and returns the access token."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": seeded_user.email, "password": DEFAULT_PASSWORD},
    )
    token: str = response.json()["access_token"]

    return token
