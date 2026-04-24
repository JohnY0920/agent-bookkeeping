"""Email sending via SendGrid."""
import asyncio
from app.config import settings


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    cc_emails: list[str] | None = None,
    reply_to: str | None = None,
) -> dict:
    """Send an email via SendGrid. Always CC the assigned accountant (enforced in comms_agent prompt)."""
    if not settings.SENDGRID_API_KEY:
        return {"status": "skipped", "reason": "SENDGRID_API_KEY not configured"}

    import httpx
    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                **({"cc": [{"email": e} for e in cc_emails]} if cc_emails else {}),
            }
        ],
        "from": {"email": settings.EMAIL_FROM},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
        **({"reply_to": {"email": reply_to}} if reply_to else {}),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            timeout=30,
        )

    if resp.status_code not in (200, 202):
        return {"status": "error", "http_status": resp.status_code, "detail": resp.text[:200]}

    return {"status": "sent", "to": to_email, "subject": subject}
