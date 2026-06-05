import random
from datetime import datetime, timezone
from typing import Optional
from app.config import get_settings

settings = get_settings()

_otp_store: dict[str, dict] = {}


def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def store_otp(email: str, otp: str):
    _otp_store[email] = {
        "otp": otp,
        "expires": datetime.now(timezone.utc).timestamp() + 600,
        "attempts": 0,
    }


def verify_otp(email: str, otp: str) -> bool:
    data = _otp_store.get(email)
    if not data:
        return False
    if datetime.now(timezone.utc).timestamp() > data["expires"]:
        return False
    if data["attempts"] >= 3:
        return False
    if data["otp"] != otp:
        data["attempts"] += 1
        return False
    del _otp_store[email]
    return True


async def send_email(to: str, subject: str, text: str) -> bool:
    import smtplib
    from email.mime.text import MIMEText

    if not settings.smtp_user:
        return False

    msg = MIMEText(text)
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)
        return True
    except Exception:
        return False
