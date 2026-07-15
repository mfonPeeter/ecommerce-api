import pytest
from sqlmodel import Session

from app.users.models import User
from app.auth.utils import get_password_hash

DEFAULT_PASSWORD = "qwertyasdf"


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
