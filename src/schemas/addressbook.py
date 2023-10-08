from datetime import date
from typing import List

import phonenumbers
from pydantic import BaseModel, EmailStr, Field, PastDate, field_validator

from src.database.models import ContactType


class ContactResponse(BaseModel):
    """
    Represents a contact response.

    Attributes:
        id (int): The unique identifier for the contact.
        contact_type (ContactType): The type of contact.
        contact_value (str): The value of the contact.

    Configured with:
        from_attributes (bool): Flag indicating if the attributes should be used for configuration.
    """

    id: int
    contact_type: ContactType
    contact_value: str

    class ConfigDict:
        from_attributes = True


class AddressbookBase(BaseModel):
    """
    Represents the base structure for an address book entry.

    Attributes:
        first_name (str): The first name of the contact.
        last_name (str): The last name of the contact (max length: 55).
    """

    first_name: str = Field(max_length=55)
    last_name: str = Field(max_length=55)


class AddressbookResponse(AddressbookBase):
    """
    Represents a response containing address book information.

    Attributes:
        id (int): The unique identifier for the address book entry.
        birthday (date): The birthday of the contact.
        contacts (List[ContactResponse]): List of contacts associated with the address book entry.

    Configured with:
        from_attributes (bool): Flag indicating if the attributes should be used for configuration.
    """

    id: int
    birthday: date
    contacts: List[ContactResponse]

    class ConfigDict:
        from_attributes = True


class AddressbookUpdateName(AddressbookBase):
    """
    Represents a request to update the name in the address book.

    Configured with:
        from_attributes (bool): Flag indicating if the attributes should be used for configuration.
    """

    class ConfigDict:
        from_attributes = True


class AddressbookCreate(AddressbookBase):
    """
    Represents a request to create a new address book entry.

    Attributes:
        birthday (PastDate): The birthday of the contact.

    """

    birthday: PastDate


class DayToBirthday(BaseModel):
    """
    Represents the number of days until a birthday.

    This class validates the number of days until a birthday, ensuring it falls within the range of 0 to 7.

    Attributes:
        day_to_birthday (int): The number of days until the birthday.

    Methods:
        validate_day_to_birthday(value: int) -> int:
            Validates the number of days until a birthday, ensuring it is within the range of 0 to 7.
            If the value is out of range, a ValueError is raised.
    """

    day_to_birthday: int

    @field_validator("day_to_birthday")
    @classmethod
    def validate_day_to_birthday(cls, value):
        """
        The validate_day_to_birthday function validates that the day_to_birthday field is between 0 and 7.


        :param cls: Pass the class that is being created
        :param value: Pass the value that is being validated
        :return: The value if it is between 0 and 7
        """

        if value < 0 or value > 7:
            raise ValueError("day_to_birthday must be between 0 and 7")
        return value


class AddressbookUpdateBirthday(BaseModel):
    """
    Represents a request to update the birthday in the address book.

    Attributes:
        birthday (PastDate): The updated birthday of the contact.

    """

    birthday: PastDate


class PhoneCreate(BaseModel):
    """
    Represents a phone number creation utility.

    This class allows for the creation and validation of phone numbers.

    Attributes:
        phone (str): The phone number to be created or validated.

    Methods:
        sanitize_phone_number(value: str) -> str:
            Sanitizes a phone number by removing non-numeric characters and adding a '+' at the beginning.

        validate_phone_number(value: str) -> str:
            Validates a phone number using the phonenumbers library.
            If the phone number is invalid, a ValueError is raised.
            If valid, returns the sanitized phone number.
    """

    phone: str

    @classmethod
    def sanitize_phone_number(cls, value):
        """
        The sanitize_phone_number function takes a phone number and removes all non-numeric characters from it.
        It then adds a + to the beginning of the string, which is required by phonenumbers.

        :param cls: Refer to the class that is being used
        :param value: Pass in the phone number that is being sanitized
        :return: A string of digits with a + at the beginning
        """
        value = "".join(filter(str.isdigit, value))
        return "+" + value

    @field_validator("phone")
    @classmethod
    def validate_phone_number(cls, value):
        """
        The validate_phone_number function takes a phone number and validates it using the phonenumbers library.
        If the phone number is invalid, an exception is raised. If the phone number is valid, it returns a sanitized version
        of that phone number.

        :param cls: Pass the class that is being used to validate the phone number
        :param value: Pass in the phone number that is being validated
        :return: The phone_number variable
        """
        phone_number = cls.sanitize_phone_number(value)
        try:
            phonenumbers.parse(phone_number, None)
            return phone_number
        except phonenumbers.phonenumberutil.NumberParseException as err:
            raise ValueError(f"{err}")


class EmailCreate(BaseModel):
    """
    Represents a request to create an email entry.

    Attributes:
        email (EmailStr): The email address.

    """

    email: EmailStr
