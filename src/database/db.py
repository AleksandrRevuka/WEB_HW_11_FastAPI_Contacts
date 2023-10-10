import contextlib
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)

from src.conf.config import settings
import asyncpg

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url


class DatabaseSessionManager:
    """
    A manager for creating and managing database sessions.

    This class provides methods to create and manage asynchronous database sessions.

    Attributes:
        _engine (AsyncEngine): The asynchronous SQLAlchemy engine.
        _session_maker (async_sessionmaker): The asynchronous session maker.

    Methods:
        __init__(self, url: str):
            Initializes the DatabaseSessionManager with a given database URL.

        session(self) -> AsyncIterator[AsyncSession]:
            A context manager that yields an asynchronous database session.

    Example:
        sessionmanager = DatabaseSessionManager(settings.sqlalchemy_database_url)
        async with sessionmanager.session() as session:
            # Use the session for database operations
    """

    def __init__(self, url: str):
        """
        Initializes the DatabaseSessionManager with a given database URL.

        :param url: The SQLAlchemy database URL.
        :type url: str
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker | None = async_sessionmaker(
            autocommit=False, autoflush=False, expire_on_commit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Provides an asynchronous context manager to yield a database session.

        Usage:
            async with sessionmanager.session() as session:
                # Use the session for database operations

        :return: An asynchronous database session.
        :rtype: AsyncSession
        """
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        session = self._session_maker()
        try:
            yield session
        except Exception as err:
            print(err)
            await session.rollback()
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.sqlalchemy_database_url)


async def get_db():
    """
    Asynchronous generator function to get a database session.

    Usage:
        async with get_db() as session:
            # Use the session for database operations

    Yields:
        AsyncSession: An asynchronous database session.
    """
    async with sessionmanager.session() as session:
        yield session
