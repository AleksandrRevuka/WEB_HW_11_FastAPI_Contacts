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
    """
    The search_contacts function searches for contacts in the user's address book.
        The search is performed on first name, last name and contact value.

    :param criteria: str: Search for a contact in the database
    :param user_addresbook: Query: Filter the results of the query
    :return: A list of abc objects
    """

    return user_addresbook.filter(
        or_(
            ABC.first_name.ilike(f"%{criteria}%"),
            ABC.last_name.ilike(f"%{criteria}%"),
            Contact.contact_value.ilike(f"%{criteria}%"),
        )
    ).all()


async def get_contacts(skip: int, limit: int, addressbook: Query) -> List[ABC]:
    """
    The get_contacts function returns a list of contacts from the addressbook.


    :param skip: int: Skip the first n contacts
    :param limit: int: Limit the number of contacts returned
    :param addressbook: Query: Filter the contacts
    :return: A list of abc objects
    """
    return addressbook.offset(skip).limit(limit).all()


async def get_contact(contact_id: int, user_addresbook: Query) -> ABC | None:
    """
    The get_contact function takes in a contact_id and returns the corresponding
    contact from the user's address book. If no such contact exists, it returns None.

    :param contact_id: int: Get the contact by id
    :param user_addresbook: Query: Filter the database for a contact with the given id
    :return: The contact with the given id
    """
    return user_addresbook.filter(ABC.id == contact_id).first()


async def create_contact(
    db: Session,
    contact_create: AddressbookCreate,
    email_create: EmailCreate,
    phone_create: PhoneCreate,
    current_user: User,
    user_addresbook: Query,
) -> ABC:
    """
    The create_contact function creates a new contact in the database.

    :param db: Session: Access the database
    :param contact_create: AddressbookCreate: Create a new contact
    :param email_create: EmailCreate: Create a new email contact
    :param phone_create: PhoneCreate: Create a new contact
    :param current_user: User: Get the current user logged in
    :param user_addresbook: Query: Query the database for a specific user's address book
    :return: The created contact
    """
    db_contact = ABC(**contact_create.model_dump())

    db_contact.user_id = current_user.id

    if db_contact:
        existing_contact = user_addresbook.filter(
            ABC.first_name == db_contact.first_name,
            ABC.last_name == db_contact.last_name,
        ).first()

        if existing_contact and existing_contact.id != db_contact.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Contact with first_name and last_name already exists!",
            )

        db.add(db_contact)
        db.commit()
        db.refresh(db_contact)

    email = user_addresbook.filter(
        Contact.contact_type == ContactType.email,
        Contact.contact_value == email_create.email,
    ).first()

    if email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is exists!")

    email = Contact(
        contact_type=ContactType.email,
        contact_value=email_create.email,
        contact_id=db_contact.id,
    )

    db.add(email)
    db.commit()
    db.refresh(email)

    phone = user_addresbook.filter(
        Contact.contact_type == ContactType.phone,
        Contact.contact_value == phone_create.phone,
    ).first()

    if phone:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!")

    phone = Contact(
        contact_type=ContactType.phone,
        contact_value=phone_create.phone,
        contact_id=db_contact.id,
    )

    db.add(phone)
    db.commit()
    db.refresh(phone)

    return db_contact


async def add_phone_to_contact(db: Session, phone_create: PhoneCreate, user_addresbook: Query, contact_id: int) -> ABC:
    """
    The add_phone_to_contact function adds a phone to the contact.
        Args:
            db (Session): The database session object.
            phone_create (PhoneCreate): The PhoneCreate schema model object.  This is used to validate the request body data and
            create a new Contact record in the database if it passes validation.
            user_addresbook (Query): A query that returns all of the contacts for a given user from their address book, including
            any associated phones or emails for each contact in their address book..  This is used to check if there are any
            existing contacts with this email or phone number already in this users'

    :param db: Session: Access the database
    :param phone_create: PhoneCreate: Get the phone number from the request body
    :param user_addresbook: Query: Filter the contact by id
    :param contact_id: int: Get the contact from the database
    :return: The contact object
    """
    contact: ABC = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        phone = user_addresbook.filter(
            Contact.contact_type == ContactType.phone,
            Contact.contact_value == phone_create.phone,
        ).first()

        if phone:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!")

        phone = Contact(contact_type=ContactType.phone, contact_value=phone_create.phone, contact_id=contact.id)

        db.add(phone)
        db.commit()
        db.refresh(phone)
    return contact


async def add_email_to_contact(db: Session, email_create: EmailCreate, user_addresbook: Query, contact_id: int) -> ABC:
    """
    The add_email_to_contact function adds an email to a contact.

    :param db: Session: Connect to the database
    :param email_create: EmailCreate: Create a new email
    :param user_addresbook: Query: Filter the contacts by user id
    :param contact_id: int: Specify the contact to which we want to add a phone number
    :return: The contact object
    """
    contact: ABC = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        email = user_addresbook.filter(
            Contact.contact_type == ContactType.email,
            Contact.contact_value == email_create.email,
        ).first()

        if email:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is exists!")

        email = Contact(contact_type=ContactType.email, contact_value=email_create.email, contact_id=contact.id)

        db.add(email)
        db.commit()
        db.refresh(email)
    return contact


async def update_contact_name(contact_id: int, body: AddressbookUpdateName, db: Session, user_addresbook: Query) -> ABC | None:
    """
    The update_contact_name function updates the first_name and last_name of a contact.

    :param contact_id: int: Identify the contact to be updated
    :param body: AddressbookUpdateName: Update the contact name
    :param db: Session: Access the database
    :param user_addresbook: Query: Filter the contacts by user_id
    :return: The contact object if the update was successful
    """
    contact: ABC = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        existing_contact: ABC = user_addresbook.filter(
            ABC.first_name == body.first_name,
            ABC.last_name == body.last_name,
        ).first()

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
    """
    The update_contact_birthday function updates the birthday of a contact in the addressbook.

    :param contact_id: int: Identify the contact that will be updated
    :param body: AddressbookUpdateBirthday: Pass the data from the request body to the function
    :param db: Session: Access the database
    :param user_addresbook: Query: Filter the contacts by user_id
    :return: The contact object
    """
    contact: ABC | None = user_addresbook.filter(ABC.id == contact_id).first()
    if contact:
        contact.birthday = body.birthday
        db.commit()
    return contact


async def remove_contact(contact_id: int, db: Session, user_addresbook: Query) -> ABC | None:
    """
    The remove_contact function removes a contact from the user's address book.
        Args:
            contact_id (int): The id of the contact to be removed.
            db (Session): A database session object used for querying and deleting contacts.
            user_addresbook (Query): A query object that filters contacts by their owner's id.

    :param contact_id: int: Identify the contact to be deleted
    :param db: Session: Pass the database session to the function
    :param user_addresbook: Query: Filter the contacts by user
    :return: The deleted contact
    """
    contact: ABC | None = user_addresbook.filter(ABC.id == contact_id).first()
    # TODO: del
    if contact:
        db.delete(contact)
        db.commit()
    return contact


async def read_contact_days_to_birthday(days_to_birthday: int, db: Session, user_addresbook: Query) -> list[ABC]:
    """
    The read_contact_days_to_birthday function returns a list of contacts with upcoming birthdays.

    :param days_to_birthday: int: Determine how many days in the future to look for upcoming birthdays
    :param db: Session: Pass the database session to the function
    :param user_addresbook: Query: Pass the user's address book to the function
    :return: A list of contacts with upcoming birthdays
    """
    today = date.today()
    end_date = today + timedelta(days=days_to_birthday)

    contacts_with_upcoming_birthday = user_addresbook.all()

    upcoming_birthday_contacts = []
    for contact in contacts_with_upcoming_birthday:
        contact_birthday = contact.birthday.replace(year=today.year)
        if today <= contact_birthday <= end_date:
            upcoming_birthday_contacts.append(contact)

    return upcoming_birthday_contacts
