from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.database.models import Contact
from src.schemas import ContactCreate, ContactUpdateBirthday, ContactUpdateName


async def get_contacts(skip: int, limit: int, db: Session) -> List[Contact]:
    return db.query(Contact).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, db: Session) -> Contact:
    return db.query(Contact).filter(Contact.id == contact_id).first()


async def create_contact(db: Session, contact_create: ContactCreate) -> Contact:
    db_contact = Contact(**contact_create.dict())

    if db_contact:
        existing_contact = (
            db.query(Contact)
            .filter(
                Contact.first_name == db_contact.first_name,
                Contact.last_name == db_contact.last_name,
            )
            .first()
        )

        if existing_contact and existing_contact.id != db_contact.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with first_name and last_name already exists!",
            )

        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)
    return db_contact


async def update_contact_name(contact_id: int, body: ContactUpdateName, db: Session):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact:
        existing_contact = (
            db.query(Contact)
            .filter(
                Contact.first_name == body.first_name,
                Contact.last_name == body.last_name,
            )
            .first()
        )

        if existing_contact and existing_contact.id != contact.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with first_name and last_name already exists!",
            )

        contact.first_name = body.first_name
        contact.last_name = body.last_name

        db.commit()
    return contact


async def update_contact_birthday(contact_id: int, body: ContactUpdateBirthday, db: Session):
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact:
        contact.birthday = body.birthday
        db.commit()
    return contact


async def remove_contact(contact_id: int, db: Session) -> Contact | None:
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return contact
