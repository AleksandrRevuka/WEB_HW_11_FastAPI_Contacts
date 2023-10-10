from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from src.database.models import User
from src.services.auth import auth_service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from httpx import AsyncClient


@pytest_asyncio.fixture()
async def token(client: AsyncClient, user: dict, session: AsyncSession, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    
    response = await client.post("/api/auth/signup", json=user)
    
    query = select(User).filter_by(email=user.get("email"))
    result = await session.execute(query)
    current_user = result.scalars().one_or_none()
    if current_user:
        current_user.confirmed = True
        await session.commit()
        
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )
    data = response.json()
    return data["access_token"]

@pytest_asyncio.fixture()
async def user_created(client: AsyncClient, user: dict, session: AsyncSession, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    
    response = await client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text
    
    query = select(User).filter_by(email=user.get("email"))
    result = await session.execute(query)
    current_user = result.scalars().one_or_none()
    if current_user:
        current_user.confirmed = False
        await session.commit()
        return current_user


@pytest.mark.asyncio
async def test_confirmed_email(user, client: AsyncClient):
    
    response = await client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text
    data = response.json()
    email = data["user"].email
    
    response = await client.get(f"/api/auth//confirmed_email/{token}")
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["message"] == "Email confirmed"