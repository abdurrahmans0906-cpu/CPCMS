import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models.notification import Notification
from app.models.user import User


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    if not settings.SMTP_ENABLED:
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM
        msg["To"] = to_email
        msg["Subject"] = f"[CPCMS] {subject}"
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception:
        # Non-blocking error in notification dispatch
        return False


def create_notification(
    db: Session,
    user_id: uuid.UUID,
    kind: str,
    message: str,
    link: Optional[str] = None
) -> Notification:
    notif = Notification(
        user_id=user_id,
        kind=kind,
        message=message,
        link=link,
        is_read=False
    )
    db.add(notif)
    db.flush()

    user = db.query(User).filter(User.id == user_id).first()
    if user and settings.SMTP_ENABLED:
        send_email_notification(user.email, kind.replace("_", " ").title(), message)

    return notif
