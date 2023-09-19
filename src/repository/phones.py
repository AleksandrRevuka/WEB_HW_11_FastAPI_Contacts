from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.database.models import Contact, Phone
from src.schemas import PhoneModel


async def create_phone(body: PhoneModel, db: Session) -> Phone:
    contact = db.query(Contact).filter_by(id=body.contact_id).first()
    phones = [phone for phone in contact.phones]
    if len(phones) > 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phone limit exceeded (maximum 3 phones allowed)")

    phone = db.query(Phone).filter_by(phone=body.phone).first()

    if phone:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Phone is exists!")

    contact = db.query(Contact).filter_by(id=body.contact_id).first()

    if not contact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found!")

    phone = Phone(phone=body.phone, contact_id=body.contact_id)

    db.add(phone)
    db.commit()
    db.refresh(phone)
    return phone
