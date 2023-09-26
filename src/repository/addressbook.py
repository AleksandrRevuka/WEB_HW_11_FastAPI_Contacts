from datetime import date, timedelta
from typing import List

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Query, Session

from src.database.models import AddressBookContact as ABC
from src.database.models import Contact, ContactType, User
from src.schemas.addressbook import (AddressbookCreate,
                                     AddressbookUpdateBirthday,
                                     AddressbookUpdateName, EmailCreate,
                                     PhoneCreate)


async def search_contacts(criteria: str, user_addresbook: Query) -> List[ABC]:

    return user_addresbook.filter(
        or_(
            ABC.first_name.ilike(f"%{criteria}%"),
            ABC.last_name.ilike(f"%{criteria}%"),
            Contact.contact_value.ilike(f"%{criteria}%")
        )
    ).all()


async def get_contacts(skip: int, limit: int, addressbook: Query) -> List[ABC]:
    return addressbook.offset(skip).limit(limit).all()


async def get_contact(contact_id: int, db: Session, user_addresbook: Query) -> ABC | None:
    return user_addresbook.filter(ABC.id == contact_id).first()


async def create_contact(
    db: Session,
    contact_create: AddressbookCreate,
    email_create: EmailCreate,
    phone_create: PhoneCreate,
    current_user: User,
    user_addresbook: Query
) -> ABC:
    db_contact = ABC(**contact_create.model_dump())
    
    db_contact.user_id = current_user.id

    if db_contact:
        existing_contact = (
            user_addresbook
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

    email = (
        user_addresbook
        .filter(
            Contact.contact_type == ContactType.email,
            Contact.contact_value == email_create.email,
        )
        .first()
    )

    if email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is exists!"
        )

    email = Contact(
        contact_type=ContactType.email,
        contact_value=email_create.email,
        contact_id=db_contact.id,
    )

    db.add(email)
    db.commit()
    db.refresh(email)

    phone = (
        user_addresbook
        .filter(
            Contact.contact_type == ContactType.phone,
            Contact.contact_value == phone_create.phone,
        )
        .first()
    )

    if phone:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!"
        )

    phone = Contact(
        contact_type=ContactType.phone,
        contact_value=phone_create.phone,
        contact_id=db_contact.id,
    )

    db.add(phone)
    db.commit()
    db.refresh(phone)

    return db_contact


async def add_phone_to_contact(db: Session, 
                               phone_create: PhoneCreate, 
                               user_addresbook: Query,
                               contact_id: int) -> ABC:
    contact: ABC = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        phone = (
        user_addresbook
        .filter(
            Contact.contact_type == ContactType.phone,
            Contact.contact_value == phone_create.phone,
        )
        .first()
        )

        if phone:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!"
            )

        phone = Contact(
            contact_type=ContactType.phone,
            contact_value=phone_create.phone,
            contact_id=contact.id
        )

        db.add(phone)
        db.commit()
        db.refresh(phone)
    return contact


async def add_email_to_contact(db: Session, 
                               email_create: EmailCreate, 
                               user_addresbook: Query,
                               contact_id: int) -> ABC:
    contact: ABC = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        email = (
        user_addresbook
        .filter(
            Contact.contact_type == ContactType.email,
            Contact.contact_value == email_create.email,
        )
        .first()
        )

        if email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email is exists!"
            )

        email = Contact(
            contact_type=ContactType.email,
            contact_value=email_create.email,
            contact_id=contact.id
        )

        db.add(email)
        db.commit()
        db.refresh(email)
    return contact
        

async def update_contact_name(
    contact_id: int, body: AddressbookUpdateName, db: Session, user_addresbook: Query
) -> ABC | None:
    contact: ABC = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        existing_contact: ABC = (
            user_addresbook
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


async def update_contact_birthday(
    contact_id: int, body: AddressbookUpdateBirthday, db: Session, user_addresbook: Query
) -> ABC | None:
    contact = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        contact.birthday = body.birthday
        db.commit()
    return contact


async def remove_contact(contact_id: int, db: Session, user_addresbook: Query) -> ABC | None:
    contact = user_addresbook.filter(ABC.id == contact_id).first()
    # TODO: del
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def read_contact_days_to_birthday(
    days_to_birthday: int, db: Session, user_addresbook: Query
) -> list[ABC]:
    today = date.today()
    end_date = today + timedelta(days=days_to_birthday)

    contacts_with_upcoming_birthday = user_addresbook.all()

    upcoming_birthday_contacts = []
    for contact in contacts_with_upcoming_birthday:
        contact_birthday = contact.birthday.replace(year=today.year)
        if today <= contact_birthday <= end_date:
            upcoming_birthday_contacts.append(contact)

    return upcoming_birthday_contacts
