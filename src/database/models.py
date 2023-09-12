from .db import Base

from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Date
from sqlalchemy.orm import relationship


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(55), nullable=False)
    last_name = Column(String(55), nullable=False)
    birthday = Column("birthday", Date)

    emails = relationship("Email", backref="contacts")
    phones = relationship("Phone", backref="contacts")


class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    email = Column(String(50), nullable=False, unique=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)

    contact = relationship("Contact", back_populates="emails")


class Phone(Base):
    __tablename__ = "phones"

    id = Column(Integer, primary_key=True)
    phone = Column(String(20), nullable=False, unique=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False)

    contact = relationship("Contact", back_populates="phones")
