from time import sleep
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = await client.post("/api/auth/signup", json=user)

    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert data["user"]["email"] == user["email"]
    assert "id" in data["user"]

    mock_send_email.assert_called_once_with(
        user["email"], "admin_test5", "http://testserver/", "Confirm your email! ", "email_template.html"
    )


@pytest.mark.asyncio
async def test_repeat_create_user(client: AsyncClient, user, monkeypatch):
    sleep(5)
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)

    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text

    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


@pytest.mark.asyncio
async def test_login_user_invalid_email(client, user):
    sleep(5)
    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text

    response = await client.post(
        "/api/auth/login",
        data={"username": "invalid_email@example.com", "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.mark.asyncio
async def test_login_user_not_confirmed(client, user):
    sleep(8)

    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text

    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password"), "confirmed": user.get("confirmed")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login_wrong_password(client, user, session):
    sleep(10)
    response = await client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text

    query = select(User).filter_by(email=user.get("email"))
    result = await session.execute(query)
    current_user = result.scalars().one_or_none()
    if current_user:
        current_user.confirmed = True
        await session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": "wrong_password", "confirmed": user.get("confirmed")},
    )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


@pytest.mark.asyncio
async def test_login_user(client, session: AsyncSession, user):
    sleep(15)
    response = await client.post("/api/auth/signup", json=user)
    assert response.status_code == 201, response.text

    query = select(User).filter_by(email=user.get("email"))
    result = await session.execute(query)
    current_user = result.scalars().one_or_none()
    if current_user:
        current_user.confirmed = True
        await session.commit()

    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"
