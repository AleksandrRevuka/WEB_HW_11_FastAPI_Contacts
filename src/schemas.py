import phonenumbers

from typing import List
from pydantic import BaseModel, Field, EmailStr, field_validator, PastDate


class EmailModel(BaseModel):
    email: EmailStr
    contact_id: int


class EmailResponse(EmailModel):
    id: int

    class Config:
        from_attributes = True


class PhoneModel(BaseModel):
    phone: str
    contact_id: int

    @classmethod
    def sanitize_phone_number(cls, value):
        value = "".join(filter(str.isdigit, value))
        return "+" + value

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, value):
        phone_number = cls.sanitize_phone_number(value)
        try:
            phonenumbers.parse(phone_number, None)
            return phone_number
        except phonenumbers.phonenumberutil.NumberParseException as err:
            raise ValueError(f"{err}")


class PhoneResponse(PhoneModel):
    id: int

    class Config:
        from_attributes = True


class ContactBase(BaseModel):
    first_name: str = Field(max_length=55)
    last_name: str = Field(max_length=55)


class ContactResponse(ContactBase):
    id: int
    birthday: PastDate
    emails: List[EmailModel]
    phones: List[PhoneModel]

    class Config:
        from_attributes = True


class ContactUpdateName(ContactBase):
    class Config:
        from_attributes = True


class ContactCreate(ContactBase):
    birthday: PastDate


class ContactUpdateBirthday(BaseModel):
    birthday: PastDate


class DayToBirthday(BaseModel):
    day_to_birthday: int

    @field_validator("day_to_birthday")
    @classmethod
    def validate_day_to_birthday(cls, value):
        if value < 0 or value > 7:
            raise ValueError("day_to_birthday must be between 0 and 7")
        return value
