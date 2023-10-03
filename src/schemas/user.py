from pydantic import BaseModel, EmailStr

from src.database.models import Role


class UserModel(BaseModel):
    username: str
    email: str
    password: str


class UserDb(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    roles: Role

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class MessageResponse(BaseModel):
    message: str = "This is a message"


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    new_password: str
    confirm_password: str
