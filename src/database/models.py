import enum

from sqlalchemy import (Column, Date, DateTime, Enum, Integer, String, event,
                        func)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from .db import Base


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(55), nullable=False)
    last_name = Column(String(55), nullable=False)
    birthday = Column("birthday", Date)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    emails = relationship("Email", backref="contacts", cascade="all, delete")
    phones = relationship("Phone", backref="contacts", cascade="all, delete")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    email = Column(String(50), nullable=False, unique=True)
    contact_id = Column(Integer, ForeignKey(Contact.id, ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), nullable=True, unique=True)
    contact_id = Column(Integer, ForeignKey(Contact.id, ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=True)
    avatar = Column(String(255), nullable=True)
    roles = Column("roles", Enum(Role), default=Role.user)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


@event.listens_for(User, "before_insert")
def before_user_add(mapper, connection, target):
    target.roles = Role.user
