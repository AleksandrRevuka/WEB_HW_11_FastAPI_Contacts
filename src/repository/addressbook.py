from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.database.models import AddressBookContact as ABC
from src.database.models import Contact, ContactType
from src.schemas.addressbook import (AddressbookCreate,
                                     AddressbookUpdateBirthday,
                                     AddressbookUpdateName, EmailCreate,
                                     PhoneCreate)


async def get_contacts(skip: int, limit: int, db: Session) -> List[ABC]:
    return db.query(ABC).offset(skip).limit(limit).all()


async def get_contact(contact_id: int, db: Session) -> ABC | None:
    return db.query(ABC).filter(ABC.id == contact_id).first()


async def create_contact(
    db: Session, contact_create: AddressbookCreate, email_create: EmailCreate, phone_create: PhoneCreate
) -> ABC:
    db_contact = ABC(**contact_create.model_dump())

    if db_contact:
        existing_contact = (
            db.query(ABC)
            .filter(
                ABC.first_name == db_contact.first_name,
                ABC.last_name == db_contact.last_name,
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

    email = db.query(Contact).filter(Contact.contact_type == ContactType.email, 
                                     Contact.contact_value == email_create.email).first()

    if email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is exists!")

    email = Contact(contact_type=ContactType.email, contact_value=email_create.email, contact_id=db_contact.id)

    db.add(email)
    db.commit()
    db.refresh(email)

    phone = db.query(Contact).filter(Contact.contact_type == ContactType.phone, 
                                     Contact.contact_value == phone_create.phone).first()

    if phone:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!")

    phone = Contact(contact_type=ContactType.phone, contact_value=phone_create.phone, contact_id=db_contact.id)

    db.add(phone)
    db.commit()
    db.refresh(phone)

    return db_contact


async def update_contact_name(contact_id: int, body: AddressbookUpdateName, db: Session) -> ABC | None:
    contact = db.query(ABC).filter(ABC.id == contact_id).first()
    if contact:
        existing_contact = (
            db.query(ABC)
            .filter(
                ABC.first_name == body.first_name,
                ABC.last_name == body.last_name,
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


async def update_contact_birthday(contact_id: int, body: AddressbookUpdateBirthday, db: Session) -> ABC | None:
    contact = db.query(ABC).filter(ABC.id == contact_id).first()
    if contact:
        contact.birthday = body.birthday
        db.commit()
    return contact


async def remove_contact(contact_id: int, db: Session) -> ABC | None:
    contact = db.query(ABC).filter(ABC.id == contact_id).first()
    # TODO: del
    if contact:
        db.delete(contact)
        db.commit()
    return contact

async def read_contact_days_to_birthday(days_to_birthday: int, db: Session) -> list[ABC]:
    today = date.today()
    end_date = today + timedelta(days=days_to_birthday)

    contacts_with_upcoming_birthday = db.query(ABC).all()

    upcoming_birthday_contacts = []
    for contact in contacts_with_upcoming_birthday:
        contact_birthday = contact.birthday.replace(year=today.year)
        if today <= contact_birthday <= end_date:
            upcoming_birthday_contacts.append(contact)

    return upcoming_birthday_contacts
