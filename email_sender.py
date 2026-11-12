import os

import httpx
import html
import tomllib

CONFIG = tomllib.load(open("sites.toml", "rb"))
MODEL = CONFIG.get("model", "gemini-3.5-flash-lite")
EMAIL_FROM = CONFIG["email_from"]
EMAIL_TO = CONFIG["email_to"]
RESEND_URL = "https://api.resend.com/emails"
async def send_email(client, subject, text):
    """Send a plain-text email (wrapped in simple HTML) through Resend."""
    body_html = (f"<div style='font-family:sans-serif'><pre style='white-space:pre-wrap;"
                 f"font-family:inherit'>{html.escape(text)}</pre></div>")
    try:
        resp = await client.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"},
            json={"from": EMAIL_FROM, "to": EMAIL_TO, "subject": subject,
                  "text": text, "html": body_html},
            timeout=15,
        )
        resp.raise_for_status()
        print(f"  Email sent: {subject}")
    except httpx.HTTPError as e:
        extra = f" - {e.response.text}" if isinstance(e, httpx.HTTPStatusError) else ""
        print(f"  Failed to send email: {e}{extra}")