from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.templating import Jinja2Templates
from fastapi_filter import FilterDepends
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
from src.schemas.search import AddressbookFilter
from src.services.auth import auth_service
from src.services.roles import RoleAccess

allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_create = RoleAccess([Role.admin, Role.moderator])
allowed_operation_update = RoleAccess([Role.admin, Role.moderator])
allowed_operation_remove = RoleAccess([Role.admin])

templates = Jinja2Templates(directory="src/templates")

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", 
            response_model=List[AddressbookResponse],
            dependencies=[Depends(allowed_operation_get)],
            description="User, moderators and admin")
async def read_contacts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), 
                        current_user: User  = Depends(auth_service.get_current_user)) -> List[ABC]:

    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
    addressbook = await repository_addressbook.get_contacts(skip, limit, user_addresbook)
    return addressbook


@router.get("/search", 
            response_model=List[AddressbookResponse],
            dependencies=[Depends(allowed_operation_get)],
            description="User, moderators and admin")
async def search_by_criteria(contacts_filter: AddressbookFilter = FilterDepends(AddressbookFilter), 
                             db: Session = Depends(get_db), 
                             current_user: User = Depends(auth_service.get_current_user)) -> List[ABC]:
    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
    addressbook = await repository_addressbook.get_contacts_filter(contacts_filter, db, user_addresbook)
    return addressbook


@router.get("/{contact_id}", 
            response_model=AddressbookResponse,
            dependencies=[Depends(allowed_operation_get)],
            description="User, moderators and admin")
async def read_contact(contact_id: int, db: Session = Depends(get_db), 
                       current_user: User = Depends(auth_service.get_current_user)) -> ABC:
    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
    contact = await repository_addressbook.get_contact(contact_id, db, user_addresbook)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


@router.post(
    "/",
    response_model=AddressbookResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin"
)
async def create_contact(
    email_create: EmailCreate,
    phone_create: PhoneCreate,
    contact_create: AddressbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> ABC:
    contact = await repository_addressbook.create_contact(db, contact_create, email_create, phone_create, current_user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put(
    "/{contact_id}",
    response_model=AddressbookResponse,
    dependencies=[Depends(allowed_operation_get)],
    description="User, moderators and admin"
)
async def update_contact_name(
    contact_id: int,
    body: AddressbookUpdateName,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
) -> ABC:
    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
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
    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
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
    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
    contact = await repository_addressbook.remove_contact(contact_id, db, user_addresbook)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.get("/birthday/{days_to_birthday}", 
            response_model=List[AddressbookResponse],
            dependencies=[Depends(allowed_operation_get)],
            description="User, moderators and admin")
async def read_contact_days_to_birthday(days_to_birthday: int = Path(ge=0, le=7), 
                                        db: Session = Depends(get_db),
                                        current_user: User = Depends(auth_service.get_current_user)):
    user_addresbook = await repository_users.get_contacts_query(current_user.id , db)
    contacts = await repository_addressbook.read_contact_days_to_birthday(days_to_birthday, db, user_addresbook)
    return contacts
