from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from app.core.config import settings
from typing import List, Dict, Any
import os

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=settings.use_credentials,
    VALIDATE_CERTS=settings.validate_certs,
)

async def send_email(subject: str, recipients: List[EmailStr], body: str, template_name: str | None = None):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_role_notification(role: str, email: EmailStr, name: str, message_text: str):
    """
    Sends a role-specific notification email.
    """
    subject = f"Notification for {role}: {name}"
    
    html = f"""
    <html>
    <body>
        <h2>Hello {name},</h2>
        <p>You have a new notification from <b>{settings.app_name}</b>.</p>
        <div style="padding: 20px; background-color: #f4f4f4; border-radius: 5px;">
            <p>{message_text}</p>
        </div>
        <p>Regards,<br>{settings.app_name} Team</p>
    </body>
    </html>
    """
    
    await send_email(subject, [email], html)
