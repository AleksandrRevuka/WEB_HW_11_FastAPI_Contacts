import enum
from datetime import date, datetime
from typing import List

from sqlalchemy import Date, DateTime, Enum, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    """

    pass


class Role(enum.Enum):
    """
    Enum representing user roles.

    Attributes:
        admin (str): Admin role.
        moderator (str): Moderator role.
        user (str): User role.
    """

    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class ContactType(enum.Enum):
    """
    Enum representing types of contacts.

    Attributes:
        email (str): Email contact type.
        phone (str): Phone contact type.
    """

    email: str = "email"
    phone: str = "phone"


class AddressBookContact(Base):
    """
    Represents a contact in the address book.

    Attributes:
        id (int): Unique identifier for the contact.
        first_name (str): First name of the contact.
        last_name (str): Last name of the contact.
        birthday (date): Birthday of the contact.
        user_id (int): User ID associated with the contact.
        created_at (datetime): Date and time of creation.
        updated_at (datetime): Date and time of the last update.
        contacts (List[Contact]): List of contacts associated with the address book.
    """

    __tablename__ = "addressbook"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(55), nullable=False)
    last_name: Mapped[str] = mapped_column(String(55), nullable=False)
    birthday: Mapped[date] = mapped_column(Date)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    contacts: Mapped[List["Contact"]] = relationship(backref="addressbook", cascade="all, delete")


class Contact(Base):
    """
    Represents a contact.

    Attributes:
        id (int): Unique identifier for the contact.
        contact_type (ContactType): Type of the contact.
        contact_value (str): Value of the contact.
        contact_id (int): ID of the associated address book contact.
        created_at (datetime): Date and time of creation.
        updated_at (datetime): Date and time of the last update.
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    contact_type: Mapped[Enum] = mapped_column("contact_type", Enum(ContactType), nullable=False)
    contact_value: Mapped[str] = mapped_column(String(50), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("addressbook.id", ondelete="CASCADE"), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    """
    Represents a user.

    Attributes:
        id (int): Unique identifier for the user.
        username (str): Username of the user.
        email (str): Email address of the user.
        confirmed (bool): Flag indicating if the email is confirmed.
        password (str): Password of the user.
        refresh_token (str): Refresh token of the user.
        avatar (str): Avatar URL of the user.
        roles (Role): Role of the user.
        created_at (datetime): Date and time of creation.
        updated_at (datetime): Date and time of the last update.
        addressbook (List[AddressBookContact]): List of address book contacts associated with the user.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    confirmed: Mapped[bool] = mapped_column(default=False)

    password: Mapped[str] = mapped_column(String(255), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(255), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    roles: Mapped[Enum] = mapped_column("roles", Enum(Role), default=Role.user)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    addressbook: Mapped[List["AddressBookContact"]] = relationship(backref="users", cascade="all, delete")
