import jwt

from app.config import settings
from app.auth.utils import get_password_hash, verify_password, create_access_token


def test_get_password_hash():
    hashed_password = get_password_hash("secret123")

    assert hashed_password != "secret123"
    assert hashed_password.startswith("$argon2")


def test_verify_password_correct():
    hashed_password = get_password_hash("secret123")
    verify_hashed = verify_password("secret123", hashed_password)

    assert verify_hashed


def test_verify_password_incorrect():
    hashed_password = get_password_hash("secret123")
    verify_hashed = verify_password("secret", hashed_password)

    assert not verify_hashed


def test_create_access_token():
    token = create_access_token(data={"sub": "test@test.com"})

    assert token is not None
    assert isinstance(token, str)

    # decode and verify the payload
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["sub"] == "test@test.com"
