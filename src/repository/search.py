from typing import List

from sqlalchemy.orm import Session

from src.database.models import Contact, Email


async def search_contact_firstname(contact_firstname: str, db: Session) -> List[Contact]:
    return db.query(Contact).filter(Contact.first_name.ilike(f"{contact_firstname}%")).all()


async def search_contact_lastname(contact_lastname: str, db: Session) -> List[Contact]:
    return db.query(Contact).filter(Contact.last_name.ilike(f"{contact_lastname}%")).all()


async def search_contact_email(contact_email: str, db: Session) -> List[Contact]:
    return db.query(Contact).join(Contact.emails).filter(Contact.emails.any(Email.email.ilike(f"{contact_email}%"))).all()
