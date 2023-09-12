from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactResponse
from src.repository import search as repository_search

router = APIRouter(prefix="/search", tags=["search_contacts"])


@router.get("/firstname/{contact_firstname}", response_model=List[ContactResponse])
async def search_contact_firstname(contact_firstname: str, db: Session = Depends(get_db)):
    contacts = await repository_search.search_contact_firstname(contact_firstname, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacts not found")
    return contacts


@router.get("/lastname/{contact_lastname}", response_model=List[ContactResponse])
async def search_contact_lastname(contact_lastname: str, db: Session = Depends(get_db)):
    contacts = await repository_search.search_contact_lastname(contact_lastname, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacts not found")
    return contacts


@router.get("/email/{contact_email}", response_model=List[ContactResponse])
async def search_contact_email(contact_email: str, db: Session = Depends(get_db)):
    contacts = await repository_search.search_contact_email(contact_email, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contacts not found")
    return contacts
