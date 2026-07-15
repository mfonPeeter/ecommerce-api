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
