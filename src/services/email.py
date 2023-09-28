from pathlib import Path

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.services.auth import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME="Desired Name",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: EmailStr, username: str, host: str, subject: str, template: str):
    """
    The send_email function sends an email to the user with a link to verify their account.
        The function takes in four arguments:
            1) email - the user's email address, which is used as both the recipient and sender of this message.
            2) username - the username that was chosen by this user when they signed up for an account. This will be displayed in
                a greeting at the top of their verification page, so it should be personalized for each individual user.
            3) host - The domain name where our website is hosted (e.g., &quot;localhost&quot; or &quot;127.0.

    :param email: EmailStr: Specify the email address of the recipient
    :param username: str: Pass the username to the template
    :param host: str: Create the link for the user to verify their email address
    :param subject: str: Set the subject of the email
    :param template: str: Specify the template to use for sending the email
    :return: A coroutine that is not awaited
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name=template)
    except ConnectionErrors as err:
        print(err)
