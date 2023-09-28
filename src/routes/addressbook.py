from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.templating import Jinja2Templates
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import AddressBookContact as ABC
from src.database.models import Role, User
from src.repository import addressbook as repository_addressbook
from src.repository import users as repository_users
from src.schemas.addressbook import (AddressbookCreate, AddressbookResponse,
                                     AddressbookUpdateBirthday,
                                     AddressbookUpdateName, EmailCreate,
                                     PhoneCreate)
from src.services.auth import auth_service
from src.services.roles import RoleAccess

allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_create = RoleAccess([Role.admin, Role.moderator])
allowed_operation_update = RoleAccess([Role.admin, Role.moderator])
allowed_operation_remove = RoleAccess([Role.admin])

templates = Jinja2Templates(directory="src/templates")

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get(
    "/",
    response_model=List[AddressbookResponse],
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin",
)
async def read_contacts(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)
) -> List[ABC]:
    """
    The read_contacts function returns a list of contacts from the addressbook.

    :param skip: int: Skip the first n records
    :param limit: int: Limit the number of contacts returned
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the user id
    :return: A list of contacts from the addressbook
    """

    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    addressbook = await repository_addressbook.get_contacts(skip, limit, user_addresbook)
    return addressbook


@router.get(
    "/search/{search}",
    response_model=List[AddressbookResponse],
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin",
)
async def search_by_criteria(
    criteria: str, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)
) -> List[ABC]:
    """
    The search_by_criteria function searches for contacts in the addressbook by a given criteria.
        The search is performed on the first name, last name and email fields of each contact.
        If no matches are found, an empty list is returned.

    :param criteria: str: Search the database for a specific contact
    :param db: Session: Get the database session
    :param current_user: User: Get the current user from the database
    :return: A list of contacts
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    addressbook = await repository_addressbook.search_contacts(criteria, user_addresbook)
    return addressbook


@router.get(
    "/{contact_id}",
    response_model=AddressbookResponse,
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin",
)
async def read_contact(
    contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)
) -> ABC:
    """
    The read_contact function returns a contact by its id.

    :param contact_id: int: Get the contact id from the url
    :param db: Session: Get the database session
    :param current_user: User: Get the user who is currently logged in
    :return: A contact object
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.get_contact(contact_id, user_addresbook)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post(
    "/",
    response_model=AddressbookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_get), Depends(RateLimiter(times=10, seconds=60))],
    description="The User, moderator and administrator have access to this action! No more than 10 requests per minute",
)
async def create_contact(
    email_create: EmailCreate,
    phone_create: PhoneCreate,
    contact_create: AddressbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> ABC:
    """
    The create_contact function creates a new contact in the addressbook.
        The function takes an AddressbookCreate object, which contains all of the information needed to create a new contact.
        It also takes an EmailCreate and PhoneCreate objects, which contain all of the information needed to create email and
        phone numbers for that contact respectively.

    :param email_create: EmailCreate: Create a new email object
    :param phone_create: PhoneCreate: Create a new phone number for the contact
    :param contact_create: AddressbookCreate: Create a contact
    :param db: Session: Get the database session
    :param current_user: User: Get the user who is logged in
    :return: The contact
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.create_contact(
        db, contact_create, email_create, phone_create, current_user, user_addresbook
    )
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post(
    "/add_phone/{contact_id}",
    response_model=AddressbookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_get), Depends(RateLimiter(times=10, seconds=60))],
    description="The User, moderator and administrator have access to this action! No more than 10 requests per minute",
)
async def add_phone_to_contact(
    contact_id: int,
    phone_create: PhoneCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> ABC:
    """
    The add_phone_to_contact function adds a phone to an existing contact.
        The function takes the following arguments:
            - contact_id: int, the id of the contact to add a phone number to.
            - phone_create: PhoneCreate, an object containing information about
                            what kind of phone number is being added and its value.

    :param contact_id: int: Identify the contact to which we want to add a phone number
    :param phone_create: PhoneCreate: Create a new phone object
    :param db: Session: Access the database
    :param current_user: User: Get the current user
    :return:The contact with the added phone
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.add_phone_to_contact(db, phone_create, user_addresbook, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post(
    "/add_email/{contact_id}",
    response_model=AddressbookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_get), Depends(RateLimiter(times=10, seconds=60))],
    description="The User, moderator and administrator have access to this action! No more than 10 requests per minute",
)
async def add_email_to_contact(
    contact_id: int,
    email_create: EmailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> ABC:
    """
    The add_email_to_contact function adds an email to a contact.
        The function takes the following parameters:
            - contact_id: int, the id of the contact to add an email address to.
            - email_create: EmailCreate, a JSON object containing information about
                            what kind of phone number is being added and its value.

    :param contact_id: int: Specify the contact to which we want to add an email
    :param email_create: EmailCreate: Create a new email object
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the current user's id
    :return: The contact with the added email
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.add_email_to_contact(db, email_create, user_addresbook, contact_id)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put(
    "/{contact_id}",
    response_model=AddressbookResponse,
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin",
)
async def update_contact_name(
    contact_id: int,
    body: AddressbookUpdateName,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> ABC:
    """
    The update_contact_name function updates the name of a contact in the address book.

    :param contact_id: int: Find the contact to update
    :param body: AddressbookUpdateName: Pass the data to be updated in the contact
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the current user from the database
    :return: The updated contact
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.update_contact_name(contact_id, body, db, user_addresbook)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch(
    "/{contact_id}",
    response_model=AddressbookResponse,
    dependencies=[Depends(allowed_operation_update)],
    description="Only moderators and admin",
)
async def update_contact_birthday(
    contact_id: int,
    body: AddressbookUpdateBirthday,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> ABC:
    """
    The update_contact_birthday function updates the birthday of a contact.
        The function takes in an id and a body, which is used to update the birthday of the contact.
        If no contact with that id exists, then it returns 404 not found.

    :param contact_id: int: Get the contact id from the url
    :param body: AddressbookUpdateBirthday: Get the new birthday from the request body
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the current user
    :param : Get the contact id
    :return: The updated contact
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.update_contact_birthday(contact_id, body, db, user_addresbook)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete(
    "/{contact_id}",
    response_model=AddressbookResponse,
    dependencies=[Depends(allowed_operation_remove)],
    description="Only admin",
)
async def remove_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> ABC:
    """
    The remove_contact function removes a contact from the addressbook.

    :param contact_id: int: Get the contact id from the url
    :param db: Session: Pass a database session to the function
    :param current_user: User: Get the current user
    :param : Get the current user
    :return: The deleted contact
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contact = await repository_addressbook.remove_contact(contact_id, db, user_addresbook)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get(
    "/birthday/{days_to_birthday}",
    response_model=List[AddressbookResponse],
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin",
)
async def read_contact_days_to_birthday(
    days_to_birthday: int = Path(ge=0, le=7),
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> List[ABC]:
    """
    The read_contact_days_to_birthday function returns a list of contacts that have their birthday in the next 7 days.

    :param days_to_birthday: int: Filter the contacts by days to birthday
    :param le: Limit the number of days to birthday
    :param db: Session: Access the database
    :param current_user: User: Get the current user from the database
    :return: A list of contacts whose birthday is in the next 7 days
    """
    user_addresbook = await repository_users.get_contacts_query(current_user.id, db)
    contacts = await repository_addressbook.read_contact_days_to_birthday(days_to_birthday, db, user_addresbook)
    return contacts
