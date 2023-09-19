from typing import List

import phonenumbers
from fastapi import Form
from pydantic import BaseModel, EmailStr, Field, PastDate, field_validator

from src.database.models import Role


class EmailCreate(BaseModel):
    email: EmailStr


class EmailModel(EmailCreate):
    contact_id: int


class EmailResponse(BaseModel):
    email: EmailStr
    contact_id: int
    id: int

    class Config:
        from_attributes = True


class PhoneCreate(BaseModel):
    phone: str

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


class PhoneModel(PhoneCreate):
    contact_id: int


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
    emails: List[EmailResponse]
    phones: List[PhoneResponse]

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


class UserModel(BaseModel):
    username: str
    email: str
    password: str

    @classmethod
    def as_form(cls, username: str = Form(...), email: str = Form(...), password: str = Form(...)) -> "UserModel":
        return cls(username=username, email=email, password=password)


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: str
    roles: Role

    class Config:
        from_attributes = True


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
