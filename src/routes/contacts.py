from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.database.models import Contact, Role, User
from src.repository import contacts as repository_contacts
from src.schemas import (ContactCreate, ContactResponse, ContactUpdateBirthday,
                         ContactUpdateName, EmailCreate, PhoneCreate)
from src.services.auth import auth_service
from src.services.roles import RoleAccess

allowed_operation_get = RoleAccess([Role.admin, Role.moderator, Role.user])
allowed_operation_create = RoleAccess([Role.admin, Role.moderator])
allowed_operation_update = RoleAccess([Role.admin, Role.moderator])
allowed_operation_remove = RoleAccess([Role.admin])

templates = Jinja2Templates(directory="src/templates")

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("/", response_model=ContactResponse, response_class=HTMLResponse)
async def read_contacts(request: Request, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)) -> List[Contact]:
    contacts = await repository_contacts.get_contacts(skip, limit, db)
    return templates.TemplateResponse("index.html", {"request": request, "title": "Contact App", "contacts": contacts})


@router.get("/{contact_id}", response_model=ContactResponse, dependencies=[Depends(allowed_operation_get)])
async def read_contact(
    contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)
) -> Contact:
    contact = await repository_contacts.get_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.post(
    "/",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allowed_operation_create)],
    description="Only moderators and admin",
)
async def create_contact(
    email_create: EmailCreate,
    phone_create: PhoneCreate,
    contact_create: ContactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> Contact:
    contact = await repository_contacts.create_contact(db, contact_create, email_create, phone_create)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.put(
    "/{contact_id}",
    response_model=ContactResponse,
    dependencies=[Depends(allowed_operation_update)],
    description="Only moderators and admin",
)
async def update_contact_name(
    contact_id: int,
    body: ContactUpdateName,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> Contact:
    contact = await repository_contacts.update_contact_name(contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.patch(
    "/{contact_id}",
    response_model=ContactResponse,
    dependencies=[Depends(allowed_operation_update)],
    description="Only moderators and admin",
)
async def update_contact_birthday(
    contact_id: int,
    body: ContactUpdateBirthday,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
) -> Contact:
    contact = await repository_contacts.update_contact_birthday(contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact


@router.delete(
    "/{contact_id}", response_model=ContactResponse, dependencies=[Depends(allowed_operation_remove)], description="Only admin"
)
async def remove_contact(
    contact_id: int, db: Session = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)
) -> Contact:
    contact = await repository_contacts.remove_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact
