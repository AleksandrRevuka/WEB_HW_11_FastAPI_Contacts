from pydantic import BaseModel, EmailStr

from src.database.models import Role


class UserModel(BaseModel):
    """
    Represents a user model.

    Attributes:
        username (str): The username of the user.
        email (str): The email address of the user.
        password (str): The password of the user.
    """

    username: str
    email: str
    password: str


class UserDb(BaseModel):
    """
    Represents a user in the database.

    Attributes:
        id (int): The unique identifier for the user.
        username (str): The username of the user.
        email (str): The email address of the user.
        avatar (str): The avatar URL of the user.
        roles (Role): The roles associated with the user.

    Configured with:
        from_attributes (bool): Flag indicating if the attributes should be used for configuration.
    """

    id: int
    username: str
    email: str
    avatar: str
    roles: Role

    class ConfigDict:
        from_attributes = True


class UserResponse(BaseModel):
    """
    Represents a response containing user information.

    Attributes:
        user (UserDb): The user information.
        detail (str): Additional detail message (default: "User successfully created").
    """

    user: UserDb
    detail: str = "User successfully created"


class MessageResponse(BaseModel):
    """
    Represents a response containing a message.

    Attributes:
        message (str): The message (default: "This is a message").
    """

    message: str = "This is a message"


class TokenModel(BaseModel):
    """
    Represents a token model.

    Attributes:
        access_token (str): The access token.
        refresh_token (str): The refresh token.
        token_type (str): The token type (default: "bearer").
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    """
    Represents a request containing an email.

    Attributes:
        email (EmailStr): The email address.
    """

    email: EmailStr


class ResetPassword(BaseModel):
    """
    Represents a reset password request.

    Attributes:
        new_password (str): The new password.
        confirm_password (str): The confirmation of the new password.
    """

    new_password: str
    confirm_password: str
