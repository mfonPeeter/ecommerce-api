import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from .schemas import UserPublicResponse, UserUpdate, UserPasswordUpdate
from app.database import SessionDep
from app.auth.dependencies import CurrentUser
from app.auth.utils import verify_password, get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=UserPublicResponse)
async def get_user(current_user: CurrentUser):
    """Get the currently authenticated user's profile."""
    logger.debug(f"Currently authenticated user: {current_user.id}")
    return current_user


@router.patch("/me", response_model=UserPublicResponse)
async def update_user(
    payload: UserUpdate, current_user: CurrentUser, session: SessionDep
):
    """Update the currently authenticated user's profile"""
    user_data = payload.model_dump(exclude_unset=True)
    user_data["updated_at"] = datetime.now(timezone.utc)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    logger.info(f"Updated user: {current_user.id}")
    return current_user


@router.patch("/me/update-password")
async def update_user_password(
    payload: UserPasswordUpdate, current_user: CurrentUser, session: SessionDep
):
    """Update the currently authenticated user's password"""
    if not (verify_password(payload.current_password, current_user.password)):
        logger.warning(
            f"Incorrect current password provided for user: {current_user.id}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    current_user.sqlmodel_update(
        {
            "password": get_password_hash(payload.new_password),
            "updated_at": datetime.now(timezone.utc),
        }
    )
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    logger.info(f"User {current_user.id} password updated")
    return {"message": "Password updated successfully"}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(session: SessionDep, current_user: CurrentUser):
    """Delete the currently authenticated user's account"""
    logger.info(f"User {current_user.id} deleted their account")
    session.delete(current_user)
    session.commit()
