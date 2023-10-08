import os

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from main import app
from src.database.db import get_db
from src.database.models import Base

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///" + os.path.join(os.getcwd(), "test.sqlite")

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingAsyncDBSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)


@pytest_asyncio.fixture(scope="function")
async def session():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestingAsyncDBSessionLocal() as session:
        yield session

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(session):
    async def override_get_db():
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest.fixture(scope="module")
def user():
    return {"username": "admin_test5", "email": "admin_test5@example.com", "password": "1234567890", "confirmed": False}
