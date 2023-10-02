from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from src.conf.config import settings

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)
AsyncDBSession = async_sessionmaker(autocommit=False, autoflush=False, bind=async_engine,  class_=AsyncSession)


async def get_db():
    """
    The get_db function is a coroutine that creates an AsyncDBSession object,
    yields it to the caller, and then closes it. It also handles any errors that
    occur during the session by rolling back the transaction and raising an HTTPException.
    
    :return: A database session object, which is used to execute sql statements
    """
    db = AsyncDBSession()
    try:
        yield db
    except SQLAlchemyError as err:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    finally:
        await db.close()
