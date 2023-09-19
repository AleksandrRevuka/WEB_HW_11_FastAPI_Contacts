from fastapi import (APIRouter, Depends, HTTPException, Request, Security,
                     status)
from fastapi.responses import HTMLResponse
from fastapi.security import (HTTPAuthorizationCredentials, HTTPBearer,
                              OAuth2PasswordRequestForm)
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import users as repository_users
from src.schemas import TokenModel, UserModel
from src.services.auth import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="src/templates")
security = HTTPBearer()


@router.get("/signup", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request, "title": "Signup"})


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def singup(form_data: UserModel = Depends(UserModel.as_form), db: Session = Depends(get_db)):
    exist_user = await repository_users.get_user_by_email(form_data.email, db)
    if exist_user:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Account already exists")
    form_data.password = auth_service.get_password_hash(form_data.password)
    new_user = await repository_users.create_user(form_data, db)

    return new_user


@router.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})


@router.post("/login", response_model=TokenModel)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    body = form_data.parse()
    print(body.username)
    print(body.password)
    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get("/refresh_token", response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
