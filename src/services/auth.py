import pickle
from datetime import datetime, timedelta
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
    r = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=0)

    def verify_password(self, plain_password, hashed_password) -> bool:
        """
        The verify_password function takes a plain-text password and hashed
        password as arguments. It then uses the CryptContext instance to verify that
        the plain-text password matches the hashed password.

        :param self: Represent the instance of the class
        :param plain_password: Get the password that was entered by the user
        :param hashed_password: Store the hashed password in the database
        :return: True if the plain_password is equal to the hashed_password
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        The get_password_hash function takes a password and returns the hashed version of it.
        The hashing algorithm is defined in the config file, which is passed to CryptContext.

        :param self: Refer to the current instance of a class
        :param password: str: Pass in the password that we want to hash
        :return: A hash of the password
        """
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        The create_access_token function creates a new access token.


        :param self: Refer to the current instance of a class
        :param data: dict: Pass the data that will be encoded into the jwt
        :param expires_delta: Optional[float]: Set the expiration time of the access token
        :return: An encoded access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        The create_refresh_token function creates a refresh token for the user.
            The function takes in two parameters: data and expires_delta.
            Data is a dictionary containing the user's id, username, email address, and password hash.
            Expires_delta is an optional parameter that sets how long the refresh token will be valid for.

        :param self: Represent the instance of the class
        :param data: dict: Pass the data that will be encoded in the jwt
        :param expires_delta: Optional[float]: Set the time until the refresh token expires
        :return: An encoded refresh token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str) -> str:
        """
        The decode_refresh_token function is used to decode the refresh token.
            The function takes in a refresh_token as an argument and returns the email of the user if successful.
            If unsuccessful, it raises an HTTPException with status code 401 (Unauthorized) and detail 'Invalid scope for token'
            or 'Could not validate credentials'.

        :param self: Represent the instance of a class
        :param refresh_token: str: Pass the refresh token to the function
        :return: The email address of the user
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload["scope"] == "refresh_token":
                email: str = payload["sub"]
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """
        The get_current_user function is a dependency that will be used in the
            protected routes. It uses the OAuth2PasswordBearer scheme to get and validate
            the users JWT token. If it is valid, then we decode it using our SECRET_KEY
            and ALGORITHM from settings.py, which are both required for decoding a JWT token.

        :param self: Refer to the class itself
        :param token: str: Pass the token that is sent in the authorization header of a request
        :param db: Session: Pass the database session to the function
        :return: A user object
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") == "access_token":
                email = payload.get("sub")
                if email is None:
                    raise credentials_exception

            else:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = self.r.get(f"user:{email}")
        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.r.set(f"user:{email}", pickle.dumps(user))
            self.r.expire(f"user:{email}", 900)
        else:
            user = pickle.loads(user)

        return user

    async def get_email_from_token(self, token: str) -> str:
        """
        The get_email_from_token function takes a token as an argument and returns the email address associated with that token.
        If the token is invalid, it raises an HTTPException.

        :param self: Represent the instance of the class
        :param token: str: Pass in the token that was sent to the user's email
        :return: The email address that is stored in the token
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid token for email verification")

    def create_email_token(self, data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token


auth_service = Auth()
