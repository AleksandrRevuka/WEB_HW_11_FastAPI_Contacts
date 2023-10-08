import unittest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import AddressBookContact, Contact, ContactType
from src.repository.addressbook import (add_email_to_contact,
                                        add_phone_to_contact, create_contact,
                                        get_contact, get_contacts,
                                        read_contact_days_to_birthday,
                                        remove_contact, search_contacts,
                                        update_contact_birthday,
                                        update_contact_name)
from src.schemas.addressbook import (AddressbookCreate,
                                     AddressbookUpdateBirthday,
                                     AddressbookUpdateName, EmailCreate,
                                     PhoneCreate)


class TestAddressBook(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.session = AsyncMock(spec=AsyncSession())
        self.current_user = 1
        self.mock_contact = self._create_mock_contact()
        self.mock_email = self._create_mock_email()
        self.mock_phone = self._create_mocke_phone()

    def tearDown(self):
        del self.session

    def _create_mock_contact(self):
        contact = AddressBookContact()
        contact.id = 1
        contact.first_name = "Alex"
        contact.last_name = "Tester"
        contact.birthday = date(year=2000, month=10, day=10)
        return contact

    def _create_mock_email(self):
        mock_email = Contact(contact_type=ContactType.email, contact_value="alex@gmail.com", contact_id=1)
        return mock_email

    def _create_mocke_phone(self):
        mock_phone = Contact(contact_type=ContactType.phone, contact_value="+380991112233", contact_id=1)
        return mock_phone

    async def test_get_contacts(self):
        contacts = [AddressBookContact(), AddressBookContact()]
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = contacts
        self.session.execute.return_value = mock_result
        result = await get_contacts(skip=0, limit=10, current_user=self.current_user, db=self.session)

        self.assertEqual(result, contacts)

    async def test_get_contact_found(self):
        contact = AddressBookContact()
        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = contact
        self.session.execute.return_value = mock_result
        result = await get_contact(contact_id=1, current_user=self.current_user, db=self.session)

        self.assertEqual(result, contact)

    async def test_get_contact_not_found(self):
        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = None
        self.session.execute.return_value = mock_result
        result = await get_contact(contact_id=1, current_user=self.current_user, db=self.session)

        self.assertIsNone(result)

    async def test_search_contacts(self):
        criteria = "Alex"
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = criteria
        self.session.execute.return_value = mock_result
        result = await search_contacts(criteria, current_user=self.current_user, db=self.session)

        self.assertEqual(result, criteria)

    async def test_create_contact(self):
        contact_create = AddressbookCreate(birthday="2000-10-06", first_name="Alex", last_name="Tester")
        email_create = EmailCreate(email="alex@gmail.com")
        phone_create = PhoneCreate(phone="380991112233")

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=None))

        with patch("src.database.models.AddressBookContact") as abc_mock:
            abc_instance_mock = MagicMock()
            abc_mock.return_value = abc_instance_mock

            result = await create_contact(
                db=self.session,
                contact_create=contact_create,
                email_create=email_create,
                phone_create=phone_create,
                current_user=self.current_user,
            )

            self.assertIsInstance(result, AddressBookContact)

    async def test_create_contact_existing_contact(self):
        contact_create = AddressbookCreate(birthday="2000-10-06", first_name="Alex", last_name="Tester")
        email_create = EmailCreate(email="alex@gmail.com")
        phone_create = PhoneCreate(phone="380991112233")

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=(1, self.mock_contact)))

        with patch("src.database.models.AddressBookContact") as abc_mock:
            abc_instance_mock = MagicMock()
            abc_mock.return_value = abc_instance_mock

            try:
                await create_contact(
                    db=self.session,
                    contact_create=contact_create,
                    email_create=email_create,
                    phone_create=phone_create,
                    current_user=self.current_user,
                )
            except HTTPException as e:
                self.assertEqual(e.detail, "Contact with first_name and last_name already exists!")
                self.assertEqual(e.status_code, 409)

    async def test_create_contact_existing_email(self):
        contact_create = AddressbookCreate(birthday="2000-10-06", first_name="Alex", last_name="Tester")
        email_create = EmailCreate(email="alex@gmail.com")
        phone_create = PhoneCreate(phone="380991112233")

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=(1, "alex@gmail.com")))

        with patch("src.database.models.AddressBookContact") as abc_mock:
            abc_instance_mock = MagicMock()
            abc_mock.return_value = abc_instance_mock

            with self.assertRaises(HTTPException) as context:
                await create_contact(
                    db=self.session,
                    contact_create=contact_create,
                    email_create=email_create,
                    phone_create=phone_create,
                    current_user=self.current_user,
                )

            self.assertEqual(context.exception.status_code, 409)

    async def test_add_phone_to_contact(self):
        phone_create = PhoneCreate(phone="380991112233")
        contact_id = 1

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=self.mock_contact))
        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))

        result = await add_phone_to_contact(
            phone_create=phone_create, contact_id=contact_id, current_user=self.current_user, db=self.session
        )

        self.assertEqual(result.contact_type, self.mock_phone.contact_type)
        self.assertEqual(result.contact_value, self.mock_phone.contact_value)
        self.assertEqual(result.contact_id, self.mock_phone.contact_id)

    async def test_add_phone_to_contact_contact_not_found(self):
        phone_create = PhoneCreate(phone="380991112233")
        contact_id = 999

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=None))

        with self.assertRaises(HTTPException) as context:
            await add_phone_to_contact(
                db=self.session, phone_create=phone_create, contact_id=contact_id, current_user=self.current_user
            )

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_add_phone_to_contact_phone_already_exists(self):
        phone_create = PhoneCreate(phone="380991112233")
        contact_id = 1

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=self.mock_contact))
        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=self.mock_phone))

        with self.assertRaises(HTTPException) as context:
            await add_phone_to_contact(
                db=self.session, phone_create=phone_create, contact_id=contact_id, current_user=self.current_user
            )

        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(context.exception.detail, "Phone already exists for the contact")

    async def test_add_email_to_contact(self):
        email_create = EmailCreate(email="alex@gmail.com")
        contact_id = 1

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=self.mock_contact))
        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))

        result = await add_email_to_contact(
            email_create=email_create, contact_id=contact_id, current_user=self.current_user, db=self.session
        )

        self.assertEqual(result.contact_type, self.mock_email.contact_type)
        self.assertEqual(result.contact_value, self.mock_email.contact_value)
        self.assertEqual(result.contact_id, self.mock_email.contact_id)

    async def test_add_email_to_contact_contact_not_found(self):
        email_create = EmailCreate(email="alex@gmail.com")
        contact_id = 999

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=None))

        with self.assertRaises(HTTPException) as context:
            await add_email_to_contact(
                db=self.session, email_create=email_create, contact_id=contact_id, current_user=self.current_user
            )

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_add_email_to_contact_email_already_exists(self):
        email_create = EmailCreate(email="alex@gmail.com")
        contact_id = 1

        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=self.mock_contact))
        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=self.mock_email))

        with self.assertRaises(HTTPException) as context:
            await add_email_to_contact(
                db=self.session, email_create=email_create, contact_id=contact_id, current_user=self.current_user
            )

        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(context.exception.detail, "Email already exists for the contact")

    async def test_update_contact_name(self):
        mock_body = AddressbookUpdateName(first_name="Alex", last_name="Tester")
        contact_id = 1

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=self.mock_contact))
        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=None))

        result = await update_contact_name(body=mock_body, contact_id=contact_id, current_user=self.current_user, db=self.session)

        self.assertEqual(result.first_name, mock_body.first_name)
        self.assertEqual(result.last_name, mock_body.last_name)

    async def test_update_contact_name_contact_not_found(self):
        mock_body = AddressbookUpdateName(first_name="Alex", last_name="Tester")
        contact_id = 999

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))

        with self.assertRaises(HTTPException) as context:
            await update_contact_name(body=mock_body, contact_id=contact_id, current_user=self.current_user, db=self.session)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_update_contact_name_already_exists(self):
        mock_body = AddressbookUpdateName(first_name="Alex", last_name="Tester")
        contact_id = 1

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=self.mock_contact))
        self.session.execute.return_value = MagicMock(fetchone=MagicMock(return_value=self.mock_contact))

        with self.assertRaises(HTTPException) as context:
            await update_contact_name(body=mock_body, contact_id=contact_id, current_user=self.current_user, db=self.session)

        self.assertEqual(context.exception.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(context.exception.detail, "Contact with the same first and last name already exists")

    async def test_update_contact_birthday(self):
        mock_body = AddressbookUpdateBirthday(birthday="2000-12-30")
        contact_id = 1

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=self.mock_contact))

        result = await update_contact_birthday(
            body=mock_body, contact_id=contact_id, current_user=self.current_user, db=self.session
        )

        self.assertEqual(result.birthday, mock_body.birthday)

    async def test_update_contact_birthday_contact_not_found(self):
        mock_body = AddressbookUpdateBirthday(birthday="2000-12-30")
        contact_id = 1

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))

        with self.assertRaises(HTTPException) as context:
            await update_contact_birthday(body=mock_body, contact_id=contact_id, current_user=self.current_user, db=self.session)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_remove_contact(self):
        contact_id = 1

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=self.mock_contact))

        result = await remove_contact(contact_id=contact_id, current_user=self.current_user, db=self.session)

        self.assertIsInstance(result, AddressBookContact)

    async def test_remove_contact_name_already_exists(self):
        contact_id = 1

        self.session.execute.return_value = MagicMock(scalar=MagicMock(return_value=None))

        with self.assertRaises(HTTPException) as context:
            await remove_contact(contact_id=contact_id, current_user=self.current_user, db=self.session)

        self.assertEqual(context.exception.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(context.exception.detail, "Contact not found")

    async def test_read_contact_days_to_birthday(self):
        days_to_birthday = 7
        current_user = 1
        today = date.today()

        upcoming_birthday_contacts = [
            AddressBookContact(id=i, user_id=current_user, birthday=today + timedelta(days=i)) for i in range(1, days_to_birthday)
        ]

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = upcoming_birthday_contacts
        self.session.execute.return_value = mock_result

        result = await read_contact_days_to_birthday(
            db=self.session, days_to_birthday=days_to_birthday, current_user=current_user
        )

        self.assertEqual(result, upcoming_birthday_contacts)


if __name__ == "__main__":
    unittest.main()
