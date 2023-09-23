from typing import List

from sqlalchemy.orm import Session, joinedload

from src.database.models import AddressBookContact as ABC
from src.database.models import Contact, ContactType


async def search_contact_firstname(contact_firstname: str, db: Session) -> List[ABC]:
    return db.query(ABC).filter(ABC.first_name.ilike(f"{contact_firstname}%")).all()


async def search_contact_lastname(contact_lastname: str, db: Session) -> List[ABC]:
    return db.query(ABC).filter(ABC.last_name.ilike(f"{contact_lastname}%")).all()


async def search_contact_email(contact_email: str, db: Session) -> List[ABC]:
    # return db.query(ABC).join(ABC.contacts).filter(ABC.contacts.any(Contact_.email.ilike(f"{contact_email}%"))).all()
    return db.query(ABC).join(ABC.contacts).options(joinedload(ABC.contacts)).filter(
        Contact.contact_type == ContactType.email,
        Contact.contact_value.ilike(f"{contact_email}%")
    ).all()