import enum
from datetime import date, datetime
from typing import List

from sqlalchemy import (Boolean, Column, Date, DateTime, Enum, Integer, String,
                        func)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey


class Base(DeclarativeBase):
    pass


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class ContactType(enum.Enum):
    email: str = "email"
    phone: str = "phone"


class AddressBookContact(Base):
    __tablename__ = "addressbook"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(55), nullable=False)
    last_name: Mapped[str] = mapped_column(String(55), nullable=False)
    birthday: Mapped[date] =  mapped_column(Date)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    contacts: Mapped[List["Contact"]] = relationship(backref="addressbook", cascade="all, delete")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_type = mapped_column("contact_type", Enum(ContactType), nullable=False)
    contact_value: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey(AddressBookContact.id, ondelete="CASCADE"), 
                                            nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    confirmed: Mapped[bool] = mapped_column(default=False)
    
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    roles = mapped_column("roles", Enum(Role), default=Role.user)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    
    addressbook: Mapped[List["AddressBookContact"]] = relationship(backref="users", cascade="all, delete")
