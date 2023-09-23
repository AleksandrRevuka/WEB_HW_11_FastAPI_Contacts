import configparser
import pathlib

from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

file_config = pathlib.Path(__file__).parent.joinpath("config.ini")
print(file_config)

config = configparser.ConfigParser()
config.read(file_config)

username = config.get("DB", "user")
password = config.get("DB", "password")
domain = config.get("DB", "domain")
port = config.get("DB", "port")
db_name = config.get("DB", "db_name")

SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{username}:{password}@{domain}:{port}/{db_name}"
)
Base = declarative_base()
engin = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
DBSession = sessionmaker(autocommit=False, autoflush=False, bind=engin)


def get_db():
    db = DBSession()
    try:
        yield db
    except SQLAlchemyError as err:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    finally:
        db.close()
