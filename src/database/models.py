from sqlalchemy import Column, Date, DateTime, Integer, String, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from .db import Base


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(55), nullable=False)
    last_name = Column(String(55), nullable=False)
    birthday = Column("birthday", Date)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    emails = relationship("Email", backref="contacts")
    phones = relationship("Phone", backref="contacts")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    email = Column(String(50), nullable=False, unique=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    contact = relationship("Contact", back_populates="emails")


class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), nullable=False, unique=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    contact = relationship("Contact", back_populates="phones")
