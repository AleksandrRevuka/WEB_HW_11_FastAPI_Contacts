from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import PhoneResponse, PhoneModel
from src.repository import phones as repository_phones

router = APIRouter(prefix="/phones", tags=["phones"])


@router.post("/", response_model=PhoneResponse)
async def create_phone(body: PhoneModel, db: Session = Depends(get_db)):
    phone = await repository_phones.create_phone(body, db)
    return phone
