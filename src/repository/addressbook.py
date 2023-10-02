from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import and_, extract, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from src.database.models import AddressBookContact as ABC
from src.database.models import Contact, ContactType
from src.schemas.addressbook import AddressbookCreate, AddressbookUpdateBirthday, AddressbookUpdateName, EmailCreate, PhoneCreate


async def search_contacts(criteria: str, current_user: int, db: AsyncSession):
    """
    The search_contacts function searches the address book for a user by first name, last name, or contact value.

    :param criteria: str: Filter the results based on a search term
    :param current_user: int: Ensure that the user is only able to search for contacts in their own address book
    :param db: AsyncSession: Pass the database connection to the function
    :return: A list of tuples
    """
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
    """
    The get_contacts function returns a list of contacts from the address book.
    The function takes in three parameters: skip, limit, and current_user.
    Skip is an integer that determines how many contacts to skip over before returning results.
    Limit is an integer that determines how many results to return after skipping over the specified number of contacts.
    Current_user is an integer representing the user whose address book we are querying.

    :param skip: int: Determine how many records to skip
    :param limit: int: Limit the number of results returned
    :param current_user: int: Filter the results by user_id
    :param db: AsyncSession: Pass the database session to the function
    :return: A list of tuples
    """
    abc_alias = aliased(ABC)
    contact_alias = aliased(Contact)
    query = select(abc_alias).join(contact_alias).where(abc_alias.user_id == current_user).offset(skip).limit(limit)
    address_book = await db.execute(query)
    result = address_book.scalars().all()
    return result


async def get_contact(db: AsyncSession, contact_id: int, current_user: int) -> ABC | None:
    """
    The get_contact function is used to retrieve a single contact from the address book.
    It takes in two parameters: db and contact_id. The db parameter is an AsyncSession object that represents the database
    connection, while the contact_id parameter is an integer representing which specific Contact we want to retrieve
    from our Address Book.
    The function returns either a single Contact or None if no such Contact exists.

    :param db: AsyncSession: Pass in the database session
    :param contact_id: int: Specify the contact id of the contact you want to retrieve
    :param current_user: int: Make sure that the user can only access their own address book
    :return: A contact from the database
    """
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
    """
    The create_contact function creates a new contact in the database.
        Args:
            db (AsyncSession): The database session to use for this operation.
            contact_create (AddressbookCreate): A pydantic model containing the data needed to create a new Contact object.

    :param db: AsyncSession: Pass the database session to the function
    :param contact_create: AddressbookCreate: Create a new contact
    :param email_create: EmailCreate: Create a new contact
    :param phone_create: PhoneCreate: Create a new phone object
    :param current_user: int: Get the current user id
    :param : Pass the database session to the function
    :return: The new contact
    """
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
    """
    The add_phone_to_contact function adds a phone number to an existing contact.

    :param db: AsyncSession: Connect to the database
    :param phone_create: PhoneCreate: Create a new phone number for the contact
    :param current_user: int: Get the current user id
    :param contact_id: int: Identify the contact that we want to add a phone number to
    :return: A contact object, which is a row in the database
    """
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
    """
    The add_email_to_contact function adds an email to a contact.

    :param db: AsyncSession: Connect to the database
    :param email_create: EmailCreate: Create a new email for the contact
    :param current_user: int: Ensure that the user is only able to add an email address to a contact
    :param contact_id: int: Identify the contact to add the email to
    :return: A contact object
    """
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
    """
    The update_contact_name function updates the first and last name of a contact.

    :param db: AsyncSession: Pass in the database session
    :param body: AddressbookUpdateName: Pass the new first and last name to the function
    :param current_user: int: Ensure that the user is only able to update their own contacts
    :param contact_id: int: Specify the id of the contact that will be updated
    :return: A contact object
    """
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
    """
    The update_contact_birthday function updates the birthday of a contact.

    :param db: AsyncSession: Create a database connection
    :param body: AddressbookUpdateBirthday: Pass the data from the request body to the function
    :param current_user: int: Ensure that the user is only able to update their own contact
    :param contact_id: int: Identify the contact to be updated
    :return: The updated contact
    """
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
    """
    The remove_contact function removes a contact from the database.

    :param db: AsyncSession: Pass the database session into the function
    :param current_user: int: Identify the user who is making the request
    :param contact_id: int: Identify the contact to be deleted
    :return: The contact that was deleted
    """
    contact_query = select(ABC).where(ABC.id == contact_id, ABC.user_id == current_user)
    existing_contact = await db.execute(contact_query)
    contact = existing_contact.scalar()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    await db.delete(contact)
    await db.commit()

    return contact


async def read_contact_days_to_birthday(db: AsyncSession, days_to_birthday: int, current_user: int):
    """
    The read_contact_days_to_birthday function returns a list of contacts that have birthdays within the next X days.

    :param db: AsyncSession: Connect to the database
    :param days_to_birthday: int: Specify the number of days to look ahead for upcoming birthdays
    :param current_user: int: Filter the results to only show contacts that belong to the current user
    :return: A list of contacts that have a birthday within the next x days
    """
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
