"""Email service — M1 console mock, M3 SMTP/SendGrid (doc 3.7)."""
import logging
from app.core.config import get_settings

log = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    settings = get_settings()
    if settings.EMAIL_MODE == "console":
        log.warning("[email:console] to=%s subject=%s body=%.200s", to, subject, body)
        print(f"[EMAIL console] to={to} subject={subject}\n{body}\n")
        return
    # M3: integrate SMTP / SendGrid here.
    log.info("Email queued to %s: %s", to, subject)
