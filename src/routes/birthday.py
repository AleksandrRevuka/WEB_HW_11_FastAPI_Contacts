from typing import List

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import birthday as repository_birthday
from src.schemas import ContactResponse

router = APIRouter(prefix="/birthday", tags=["birthday"])


@router.get("/{days_to_birthday}", response_model=List[ContactResponse])
async def read_contact_days_to_birthday(days_to_birthday: int = Path(ge=0, le=7), db: Session = Depends(get_db)):
    contacts = await repository_birthday.read_contact_days_to_birthday(days_to_birthday, db)
    return contacts
