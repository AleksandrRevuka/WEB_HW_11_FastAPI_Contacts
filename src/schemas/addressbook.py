from datetime import date
from typing import List

import phonenumbers
from pydantic import BaseModel, EmailStr, Field, PastDate, validator

from src.database.models import ContactType


class ContactResponse(BaseModel):
    id: int
    contact_type: ContactType
    contact_value: str

    class Config:
        from_attributes = True


class AddressbookBase(BaseModel):
    first_name: str = Field(max_length=55)
    last_name: str = Field(max_length=55)


class AddressbookResponse(AddressbookBase):
    id: int
    birthday: date
    contacts: List[ContactResponse]

    class Config:
        from_attributes = True


class AddressbookUpdateName(AddressbookBase):
    class Config:
        from_attributes = True


class AddressbookCreate(AddressbookBase):
    birthday: PastDate


class DayToBirthday(BaseModel):
    day_to_birthday: int

    @validator('day_to_birthday', pre=True, always=True)
    def validate_day_to_birthday(cls, value):
        if value < 0 or value > 7:
            raise ValueError("day_to_birthday must be between 0 and 7")
        return value


class AddressbookUpdateBirthday(BaseModel):
    birthday: PastDate


class PhoneCreate(BaseModel):
    phone: str

    @classmethod
    def sanitize_phone_number(cls, value):
        value = "".join(filter(str.isdigit, value))
        return "+" + value

    
    @validator("phone", pre=True, always=True)
    def validate_phone_number(cls, value):
        phone_number = cls.sanitize_phone_number(value)
        try:
            phonenumbers.parse(phone_number, None)
            return phone_number
        except phonenumbers.phonenumberutil.NumberParseException as err:
            raise ValueError(f"{err}")


class EmailCreate(BaseModel):
    email: EmailStr
