from fastapi import (APIRouter, BackgroundTasks, Depends, HTTPException,
                     Request, Security, status)
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordRequestForm)
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.schemas.user import (RequestEmail, ResetPassword, TokenModel,
                              UserModel, UserResponse)
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)) -> dict:
    """
    The signup function creates a new user in the database.
    It takes a UserModel object as input, which contains the username and email of the new user.
    The function also takes an optional db parameter, which is used to access our database session.
    If no db parameter is passed into signup(), it will use Depends() to get one from get_db().


    :param body: UserModel: Get the data from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the server
    :param db: Session: Get the database session
    :return: A dict with the user and a message
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    subject = "Confirm your email! "
    template = "email_template.html"
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url, subject, template)
    return {"user": new_user, "detail": "User successfully created. Check your email for confirmation."}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    """
    The login function is used to authenticate a user.
    It takes in the username and password of the user, and returns an access token if successful.


    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: Session: Pass the database session to the function
    :return: A dict with the access token, refresh token and a bearer type
    """
    user: User | None = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    access_token: str = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token: str = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)) -> dict:
    """
    The refresh_token function is used to refresh the access token.
    It takes in a refresh token and returns a new access token.
    The function first decodes the refresh_token to get the email of the user who sent it, then gets that user from our database.
    If we find that their current stored refresh_token does not match what they sent us, we update their stored tokens with None
    (logging them out) and raise an HTTPException indicating unauthorized access.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the header
    :param db: Session: Pass the database session to the function
    :return: A dictionary with the access token, refresh token, and type of bearer
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user:
        if user.refresh_token != token:
            await repository_users.update_token(user, None, db)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    if user:
        await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.patch("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)) -> dict:
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        Then, it checks if that user exists in our database and if they have already confirmed their email.
        If not, then we update their record in our database with a confirmation of their email.

    :param token: str: Get the token from the url
    :param db: Session: Access the database
    :return: A message that the email is already confirmed or a message that the email has been confirmed
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)
) -> dict:
    """
    The request_email function is used to send an email to the user with a link
    to confirm their email. The function takes in the body of the request, which
    contains only one field: &quot;email&quot;. It then checks if there is a user with that
    email address and sends them an email if they exist. If not, it returns a message
    saying no such user exists.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the server
    :param db: Session: Get the database session
    :return: A message that is displayed to the user
    """
    user = await repository_users.get_user_by_email(body.email, db)
        
    if user and not user.confirmed:
        subject = "Confirm your email! "
        template = "email_template.html"
        background_tasks.add_task(send_email, user.email, user.username, request.base_url, subject, template)
        return {"message": "Check your email for confirmation."}
    else:
        return {"message": "Your email is already confirmed."}


@router.post("/request_password")
async def request_password(
    body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)
) -> dict:
    """
    The request_password function is used to request a password reset.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Get the database session from the dependency injection container
    :return: A message to the user if the email is found in our database
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user:
        subject = "Password Reset Request"
        template = "password_template.html"

        background_tasks.add_task(send_email, user.email, user.username, request.base_url, subject, template)
        return {"message": "Password reset request sent. We've emailed you with instructions on how to reset your password."}

    return {"message": "No user found with the provided email."}


@router.patch("/reset_password/{token}", response_model=UserResponse)
async def confirmed_password(body: ResetPassword, token: str, db: Session = Depends(get_db)) -> dict:
    """
    The confirmed_password function is used to reset a user's password.
        It takes in the new_password and confirm_password fields from the ResetPassword model,
        as well as a token that was sent to the user's email address. The function then checks if
        both passwords are identical, and if they are not it raises an HTTPException with status code 400 (Bad Request)
        and detail &quot;Password mismatch. Please make sure that the entered passwords are identical.&quot;
        If both passwords match, it gets the email associated with this token using auth_service.get_email_from_token(token

    :param body: ResetPassword: Get the new password and confirm_password from the request body
    :param token: str: Get the email of the user who requested a password reset
    :param db: Session: Access the database
    :return: A dictionary with the user and a message
    """
    if body.new_password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password mismatch. Please make sure that the entered passwords are identical.",
        )

    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")

    body.confirm_password = auth_service.get_password_hash(body.confirm_password)
    user = await repository_users.change_password(user, body, db)

    return {"user": user, "detail": "Password reset complete!"}
