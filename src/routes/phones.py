from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import phones as repository_phones
from src.schemas import PhoneModel, PhoneResponse

router = APIRouter(prefix="/phones", tags=["phones"])


@router.post("/", response_model=PhoneResponse, status_code=status.HTTP_201_CREATED)
async def create_phone(body: PhoneModel, db: Session = Depends(get_db)):
    phone = await repository_phones.create_phone(body, db)
    return phone
