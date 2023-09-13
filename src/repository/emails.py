from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.database.models import Contact, Email
from src.schemas import EmailModel


async def create_email(body: EmailModel, db: Session) -> Email:
    email = db.query(Email).filter(Email.email == body.email).first()

    if email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is exists!")

    contact = db.query(Contact).filter_by(id=body.contact_id).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found!")

    email = Email(email=body.email, contact_id=body.contact_id)

    db.add(email)
    db.commit()
    db.refresh(email)
    return email
