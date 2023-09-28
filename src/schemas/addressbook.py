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

    @validator("day_to_birthday", pre=True, always=True)
    def validate_day_to_birthday(cls, value: int) -> int:
        """
        The validate_day_to_birthday function validates that the day_to_birthday field is between 0 and 7.


        :param cls: Pass the class object to the function
        :param value: Pass in the value that is being validated
        :return: The value if it is between 0 and 7
        """
        if value < 0 or value > 7:
            raise ValueError("day_to_birthday must be between 0 and 7")
        return value


class AddressbookUpdateBirthday(BaseModel):
    birthday: PastDate


class PhoneCreate(BaseModel):
    phone: str

    @classmethod
    def sanitize_phone_number(cls, value) -> str:
        """
        The sanitize_phone_number function takes a phone number and removes all non-numeric characters.
        It then adds a + to the beginning of the string, which is required by phonenumbers.

        :param cls: Pass the class in which the function is being used
        :param value: Pass the phone number to be sanitized
        :return: A string of digits with a "+" at the beginning
        """
        value = "".join(filter(str.isdigit, value))
        return "+" + value

    @validator("phone", pre=True, always=True)
    def validate_phone_number(cls, value) -> str:
        """
        The validate_phone_number function takes a phone number and validates it using the phonenumbers library.
        The function first sanitizes the phone number by removing all non-numeric characters, then uses the parse() method from
        the phonenumbers library to validate that it is a valid phone number. If so, it returns the sanitized value; if not,
        it raises an error.

        :param cls: Pass the class name to the function
        :param value: Pass the phone number that is being validated
        :return: A phone number that is valid
        """
        phone_number = cls.sanitize_phone_number(value)
        try:
            phonenumbers.parse(phone_number, None)
            return phone_number
        except phonenumbers.phonenumberutil.NumberParseException as err:
            raise ValueError(f"{err}")


class EmailCreate(BaseModel):
    email: EmailStr
