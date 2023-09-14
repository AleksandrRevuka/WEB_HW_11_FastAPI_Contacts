from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.repository import emails as repository_emails
from src.schemas import EmailModel, EmailResponse

router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/", response_model=EmailResponse, status_code=status.HTTP_201_CREATED)
async def create_email(body: EmailModel, db: Session = Depends(get_db)):
    email = await repository_emails.create_email(body, db)
    return email
