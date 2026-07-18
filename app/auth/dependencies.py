import uuid
import jwt
import logging
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlmodel import select

from app.config import settings
from app.database import SessionDep
from app.users.models import User, UserRole

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token missing sub claim")
            raise credentials_exception

        user_id = uuid.UUID(user_id)

    except (InvalidTokenError, ValueError):
        logger.warning("Invalid or expired token")
        raise credentials_exception

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        logger.warning("Authenticated user not found in database")
        raise credentials_exception
    logger.debug(f"Authenticated user: {user.email}")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_vendor(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.VENDOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this resource",
        )
    return current_user


CurrentVendor = Annotated[User, Depends(require_vendor)]
