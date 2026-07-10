from sqlmodel import SQLModel

from app.users.schemas import UserPublicResponse


class AuthPublicResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublicResponse
