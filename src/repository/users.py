from libgravatar import Gravatar
from sqlalchemy.orm import Session

from src.database.models import User
from src.schemas.user import UserModel


async def get_user_by_email(email: str, db: Session) -> User | None:
    return db.query(User).filter_by(email=email).first()


async def create_user(body: UserModel, db: Session):
    g = Gravatar(body.email)
    avatar = g.get_image()
    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token, db: Session):
    user.refresh_token = refresh_token
    db.commit()
