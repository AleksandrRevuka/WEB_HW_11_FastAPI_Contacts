import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.schemas.user import UserDb
from src.services.auth import auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/", response_model=UserDb)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)) -> User:
    """
    The read_users_me function is a GET endpoint that returns the current user's information.

    :param current_user: User: Get the current user from the database
    :return: The current user object
    """
    return current_user


@router.patch("/avatar", response_model=UserDb)
async def update_avatar_user(
    file: UploadFile = File(), current_user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)
) -> User:
    """
    The update_avatar_user function takes in a file, current_user and db as parameters.
    The function then uploads the file to cloudinary using the username of the user as its public id.
    It then builds a url for that image with specific dimensions and crops it to fill those dimensions.
    Finally, it updates the avatar field in our database with this new url.

    :param file: UploadFile: Upload the file to cloudinary
    :param current_user: User: Get the current user's email
    :param db: Session: Get the database session
    :return: A user object with the new avatar url
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    r = cloudinary.uploader.upload(file.file, public_id=f"ContactsApp/{current_user.username}", overwrite=True)
    src_url = cloudinary.CloudinaryImage(f"ContactsApp/{current_user.username}").build_url(
        width=250, height=250, crop="fill", version=r.get("version")
    )
    user = await repository_users.update_avatar(current_user.email, src_url, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found for updating avatar")
    return user
