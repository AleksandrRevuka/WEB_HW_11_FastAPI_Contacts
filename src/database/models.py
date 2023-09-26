import enum

from sqlalchemy import (Boolean, Column, Date, DateTime, Enum, Integer, String,
                        func)
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from .db import Base


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class ContactType(enum.Enum):
    email = "email"
    phone = "phone"


class AddressBookContact(Base):
    __tablename__ = "addressbook"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(55), nullable=False)
    last_name = Column(String(55), nullable=False)
    birthday = Column("birthday", Date)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    contacts = relationship("Contact", backref="addressbook", cascade="all, delete")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)
    contact_type = Column("contact_type", Enum(ContactType), nullable=False)
    contact_value = Column(String(50), nullable=False)
    contact_id = Column(
        Integer, ForeignKey(AddressBookContact.id, ondelete="CASCADE"), nullable=False
    )

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(150), nullable=False, unique=True)
    confirmed = Column(Boolean, default=False)
    
    password = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=True)
    avatar = Column(String(255), nullable=True)
    roles = Column("roles", Enum(Role), default=Role.user)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    addressbook = relationship("AddressBookContact", backref="users", cascade="all, delete")
