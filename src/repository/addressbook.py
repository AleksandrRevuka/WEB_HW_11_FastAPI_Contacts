from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, extract, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database.models import AddressBookContact as ABC
from src.database.models import Contact, ContactType
from src.schemas.addressbook import AddressbookCreate, AddressbookUpdateBirthday, AddressbookUpdateName, EmailCreate, PhoneCreate


async def search_contacts(criteria: str, current_user: int, db: AsyncSession):
    query = (
        select(ABC)
        .join(Contact)
        .where(
            and_(
                ABC.user_id == current_user,
                or_(
                    ABC.first_name.ilike(f"%{criteria}%"),
                    ABC.last_name.ilike(f"%{criteria}%"),
                    Contact.contact_value.ilike(f"%{criteria}%"),
                ),
            )
        )
        .distinct()
    )

    address_book = await db.execute(query)
    result = address_book.scalars().all()
    return result


async def get_contacts(skip: int, limit: int, current_user: int, db: AsyncSession):
    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)
    query = select(abc_alias).join(contact_alias).where(abc_alias.user_id == current_user).offset(skip).limit(limit)
    address_book = await db.execute(query)
    result = address_book.scalars().all()
    return result


async def get_contact(db: AsyncSession, contact_id: int, current_user: int) -> ABC | None:
    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)
    query = select(abc_alias).join(contact_alias).where(and_(abc_alias.user_id == current_user, abc_alias.id == contact_id))

    address_book = await db.execute(query)
    result = address_book.scalars().one_or_none()

    return result


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
        query = (
            select(abc_alias)
            .join(contact_alias)
            .where(
                and_(
                    abc_alias.user_id == current_user,
                    abc_alias.first_name == db_contact.first_name,
                    abc_alias.last_name == db_contact.last_name,
                )
            )
        )

        contact = await db.execute(query)
        existing_contact = contact.fetchone()
        print(existing_contact)
        if existing_contact and existing_contact[0] != db_contact.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with first_name and last_name already exists!",
            )

        query = (
            select(abc_alias)
            .join(contact_alias)
            .where(
                and_(
                    abc_alias.user_id == current_user,
                    Contact.contact_type == ContactType.email,
                    Contact.contact_value == email_create.email,
                )
            )
        )
        emails = await db.execute(query)
        existing_email = emails.fetchone()

        if existing_email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is exists!")

        query = (
            select(abc_alias)
            .join(contact_alias)
            .where(
                and_(
                    abc_alias.user_id == current_user,
                    Contact.contact_type == ContactType.phone,
                    Contact.contact_value == phone_create.phone,
                )
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


async def add_phone_to_contact(db: AsyncSession, phone_create: PhoneCreate, current_user: int, contact_id: int) -> Contact | None:
    contact = await db.execute(select(ABC).where(ABC.id == contact_id, ABC.user_id == current_user))
    existing_contact = contact.fetchone()

    if not existing_contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    phone_query = select(Contact).where(
        Contact.contact_type == ContactType.phone,
        Contact.contact_value == phone_create.phone,
        Contact.contact_id == contact_id,
    )
    existing_phone = await db.execute(phone_query)
    if existing_phone.scalar():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists for the contact")

    new_phone = Contact(
        contact_type=ContactType.phone,
        contact_value=phone_create.phone,
        contact_id=contact_id,
    )
    db.add(new_phone)
    await db.commit()
    await db.refresh(new_phone)

    return new_phone


async def add_email_to_contact(db: AsyncSession, email_create: EmailCreate, current_user: int, contact_id: int) -> Contact:
    contact = await db.execute(select(ABC).where(ABC.id == contact_id, ABC.user_id == current_user))
    existing_contact = contact.fetchone()

    if not existing_contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    email_query = select(Contact).where(
        Contact.contact_type == ContactType.email,
        Contact.contact_value == email_create.email,
        Contact.contact_id == contact_id,
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
    await db.commit()
    await db.refresh(new_email)

    return new_email


async def update_contact_name(db: AsyncSession, body: AddressbookUpdateName, current_user: int, contact_id: int):
    contact_query = select(ABC).where(ABC.id == contact_id, ABC.user_id == current_user)
    existing_contact = await db.execute(contact_query)
    contact = existing_contact.scalar()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    existing_name_query = select(ABC).where(
        ABC.first_name == body.first_name,
        ABC.last_name == body.last_name,
        ABC.user_id == current_user,
    )
    existing_name = await db.execute(existing_name_query)
    if existing_name.scalar():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contact with the same first and last name already exists",
        )

    contact.first_name = body.first_name
    contact.last_name = body.last_name
    await db.commit()
    await db.refresh(contact)

    return contact


async def update_contact_birthday(
    db: AsyncSession, body: AddressbookUpdateBirthday, current_user: int, contact_id: int
) -> ABC | None:
    contact_query = select(ABC).where(ABC.id == contact_id, ABC.user_id == current_user)
    existing_contact = await db.execute(contact_query)
    contact = existing_contact.scalar()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    contact.birthday = body.birthday
    await db.commit()
    await db.refresh(contact)

    return contact


async def remove_contact(db: AsyncSession, current_user: int, contact_id: int) -> ABC | None:
    contact_query = select(ABC).where(ABC.id == contact_id, ABC.user_id == current_user)
    existing_contact = await db.execute(contact_query)
    contact = existing_contact.scalar()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    await db.delete(contact)
    await db.commit()

    return contact


async def read_contact_days_to_birthday(db: AsyncSession, days_to_birthday: int, current_user: int):
    today = date.today()
    end_date = today + timedelta(days=days_to_birthday)

    upcoming_birthday_contacts_query = (
        select(ABC)
        .where(
            and_(
                ABC.user_id == current_user,
                ABC.birthday.isnot(None),
                extract("month", ABC.birthday) == end_date.month,
                extract("day", ABC.birthday) <= end_date.day,
                extract("month", ABC.birthday) >= today.month,
            )
        )
        .order_by(ABC.birthday)
    )
    upcoming_birthday_contacts = await db.execute(upcoming_birthday_contacts_query)
    results = upcoming_birthday_contacts.scalars().all()

    filtered_results = [contact for contact in results if (contact.birthday - today).days <= days_to_birthday]

    return filtered_results
