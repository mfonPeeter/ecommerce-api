from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlalchemy.exc import MultipleResultsFound

from .schemas import AuthPublicResponse
from .utils import get_password_hash, create_access_token, verify_password
from app.users.schemas import UserCreate
from app.users.models import User
from app.database import SessionDep

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/register", response_model=AuthPublicResponse, status_code=status.HTTP_201_CREATED
)
async def register(payload: UserCreate, session: SessionDep):
    try:
        existing_user = session.exec(
            select(User).where(User.email == payload.email)
        ).one_or_none()
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data integrity error",
        )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already exists"
        )

    hashed_password = get_password_hash(payload.password)
    user = User.model_validate(payload, update={"password": hashed_password})
    session.add(user)
    session.commit()
    session.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    return AuthPublicResponse(access_token=access_token, user=user)


@router.post("/login", response_model=AuthPublicResponse)
async def login(
    payload: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep
):
    try:
        user = session.exec(
            select(User).where(User.email == payload.username)
        ).one_or_none()
    except MultipleResultsFound:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data integrity error",
        )

    if not (user and verify_password(payload.password, user.password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return AuthPublicResponse(access_token=access_token, user=user)
