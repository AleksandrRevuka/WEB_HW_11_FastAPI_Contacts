from datetime import date, timedelta
from typing import List, Tuple

from fastapi import HTTPException, status
from sqlalchemy import Result, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database.models import AddressBookContact as ABC
from src.database.models import Contact, ContactType, User
from src.schemas.addressbook import (AddressbookCreate, AddressbookResponse,
                                     AddressbookUpdateBirthday,
                                     AddressbookUpdateName, ContactResponse,
                                     EmailCreate, PhoneCreate)


async def search_contacts(criteria: str, current_user: int, db: AsyncSession) -> List[ABC]:

    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)

    query = select(abc_alias).join(contact_alias).where(
        and_(
            abc_alias.user_id == current_user,
            or_(
                abc_alias.first_name.ilike(f"%{criteria}%"),
                abc_alias.last_name.ilike(f"%{criteria}%"),
                contact_alias.contact_value.ilike(f"%{criteria}%"),
            )
        )
    )

    address_book = await db.execute(query)
    result = address_book.fetchall()
    return [ABC(**item.__dict__) for item in result]


async def get_contacts(skip: int, limit: int, current_user: int, db: AsyncSession) -> List[ABC]:

    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)
    query = select(abc_alias).join(contact_alias).where(
        abc_alias.user_id == current_user).offset(skip).limit(limit)
    address_book = await db.execute(query)
    result = address_book.fetchall()
    return [ABC(
        id=item.id,
        first_name=item.first_name,
        last_name=item.last_name,
        birthday=item.birthday,
        user_id=item.user_id,
        contacts=item.contacts
    ) for item in result]


async def get_contact(db: AsyncSession, contact_id: int, current_user: int) -> ABC | None:
    
    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)
    query = select(abc_alias).join(contact_alias).where(
        and_(
            abc_alias.user_id == current_user, 
            abc_alias.id == contact_id
        )
    )
        
    address_book = await db.execute(query)
    result = address_book.fetchone()
    
    return ABC(**result.__dict__)


async def create_contact(
    db: AsyncSession,
    contact_create: AddressbookCreate,
    email_create: EmailCreate,
    phone_create: PhoneCreate,
    current_user: int, 
) -> ABC:
    db_contact = ABC(**contact_create.model_dump())

    db_contact.user_id = current_user
    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)

    if db_contact:
        query = select(abc_alias).join(contact_alias).where(
            and_(
            abc_alias.user_id == current_user,
            abc_alias.first_name == db_contact.first_name,
            abc_alias.last_name == db_contact.last_name,
            )
        )

        contact = await db.execute(query)
        existing_contact = contact.fetchone()
        if existing_contact and existing_contact.id != db_contact.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with first_name and last_name already exists!",
            )

        query = select(abc_alias).join(contact_alias).where(
            and_(
                abc_alias.user_id == current_user,
                Contact.contact_type == ContactType.email,
                Contact.contact_value == email_create.email,
            )
        )
        emails = await db.execute(query)
        existing_email = emails.fetchone()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is exists!")

        query = select(abc_alias).join(contact_alias).where(
            and_(
                abc_alias.user_id == current_user,
                Contact.contact_type == ContactType.phone,
                Contact.contact_value == phone_create.phone,
            )
        )
        phones = await db.execute(query)
        existing_phone = phones.fetchone()

        if existing_phone:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!")


    db.add(db_contact)
    await db.commit()
    await db.refresh(db_contact)

    email = Contact(
        contact_type=ContactType.email,
        contact_value=email_create.email,
        contact_id=db_contact.id,
    )

    db.add(email)
    await db.commit()
    await db.refresh(email)

    phone = Contact(
        contact_type=ContactType.phone,
        contact_value=phone_create.phone,
        contact_id=db_contact.id,
    )
    
    db.add(phone)
    await db.commit()
    await db.refresh(phone)

    return db_contact


async def add_phone_to_contact(db: AsyncSession, phone_create: PhoneCreate, current_user: int, contact_id: int) -> ABC | None:

    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)
    query = select(abc_alias).join(contact_alias).where(
        and_(
            abc_alias.user_id == current_user,
            abc_alias.id == contact_id,
            Contact.contact_type == ContactType.phone,
            Contact.contact_value == phone_create.phone,
        )
    )
    existing_contact = await db.execute(query)
    contact = existing_contact.fetchone()
    
    if contact:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!")
    
    query = select(abc_alias).join(contact_alias).where(
        and_(
            abc_alias.user_id == current_user,
            abc_alias.id == contact_id,
        )
    )
    existing_contact = await db.execute(query)
    contact = existing_contact.fetchone()
    if contact:
        phone = Contact(contact_type=ContactType.phone, contact_value=phone_create.phone, contact_id=contact.id)

    db.add(phone)
    await db.commit()
    await db.refresh(phone)

    return ABC(**contact.__dict__)


async def add_email_to_contact(db: AsyncSession, email_create: EmailCreate, current_user: int, contact_id: int) -> ABC:

    async with db.begin() as conn:
        contact = await db.execute(select(ABC).filter(ABC.id == contact_id, ABC.user_id == current_user))
        existing_contact = contact.fetchone()

        if not existing_contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

        email_query = (
            select(Contact)
            .where(
                Contact.contact_type == ContactType.email,
                Contact.contact_value == email_create.email,
                Contact.contact_id == contact_id,
            )
        )
        existing_email = await db.execute(email_query)
        if existing_email.scalar():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists for the contact")

        new_email = Contact(
            contact_type=ContactType.email,
            contact_value=email_create.email,
            contact_id=contact_id,
        )
        db.add(new_email)
        await conn.commit()
        await db.refresh(new_email)

        return ABC(**existing_contact.__dict__)


async def update_contact_name(
    db: AsyncSession, body: AddressbookUpdateName, current_user: int, contact_id: int
) -> ABC:
    async with db.begin() as conn:
        contact_query = select(ABC).filter(ABC.id == contact_id, ABC.user_id == current_user)
        existing_contact = await db.execute(contact_query)
        contact = existing_contact.fetchone()

        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

        existing_name_query = (
            select(ABC)
            .filter(
                ABC.first_name == body.first_name,
                ABC.last_name == body.last_name,
                ABC.id != contact_id,
                ABC.user_id == current_user,
            )
        )
        existing_name = await db.execute(existing_name_query)
        if existing_name.scalar():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with the same first and last name already exists",
            )

        contact.first_name = body.first_name
        contact.last_name = body.last_name
        await conn.commit()
        await db.refresh(contact)

        return ABC(**contact.__dict__)


async def update_contact_birthday(db: AsyncSession, body: AddressbookUpdateBirthday, 
                                  current_user: int, contact_id: int) -> ABC | None:

    async with db.begin() as conn:
        contact_query = select(ABC).filter(ABC.id == contact_id, ABC.user_id == current_user)
        existing_contact = await db.execute(contact_query)
        contact = existing_contact.fetchone()

        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

        contact.birthday = body.birthday
        await conn.commit()
        await db.refresh(contact)

        return ABC(**contact.__dict__)


async def remove_contact(db: AsyncSession, current_user: int, contact_id: int) -> ABC | None:
    async with db.begin() as conn:
        contact_query = select(ABC).filter(ABC.id == contact_id, ABC.user_id == current_user)
        existing_contact = await db.execute(contact_query)
        contact = existing_contact.fetchone()

        if not contact:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

        await db.delete(contact)
        await conn.commit()

        return ABC(**contact.__dict__)


async def read_contact_days_to_birthday(db: AsyncSession, 
                                        days_to_birthday: int, 
                                        current_user: int) -> List[ABC]:
    today = date.today()
    end_date = today + timedelta(days=days_to_birthday)

    end_month_day = (end_date.month, end_date.day)

    month_day_filter = or_(
        and_(ABC.birthday.month < end_month_day[0], 
             ABC.birthday.month >= today.month),
        and_(
            ABC.birthday.month == end_month_day[0],
            ABC.birthday.day <= end_month_day[1],
            ABC.birthday.month >= today.month,
        ),
    )
    upcoming_birthday_contacts_query = (
        select(ABC)
        .where(
            and_(
                ABC.user_id == current_user,
                ABC.birthday.isnot(None),
                month_day_filter,
            )
        )
        .order_by(ABC.birthday)
    )
    upcoming_birthday_contacts = await db.execute(upcoming_birthday_contacts_query)
    result = upcoming_birthday_contacts.fetchall()
    return [ABC(**item.__dict__) for item in result]