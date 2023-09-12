from sqlalchemy.orm import Session
from datetime import date, timedelta

from src.database.models import Contact


async def read_contact_days_to_birthday(days_to_birthday: int, db: Session) -> list[Contact]:
    today = date.today()
    end_date = today + timedelta(days=days_to_birthday)

    contacts_with_upcoming_birthday = db.query(Contact).all()

    upcoming_birthday_contacts = []
    for contact in contacts_with_upcoming_birthday:
        contact_birthday = contact.birthday.replace(year=today.year)
        if today <= contact_birthday <= end_date:
            upcoming_birthday_contacts.append(contact)

    return upcoming_birthday_contacts
