import os
import smtplib
from email.message import EmailMessage

class EmailService:
    """
    Email sending utility for development/testing environments.
    This module provides EmailService, a thin wrapper around Python's smtplib and
    email.message.EmailMessage to send plain-text emails. It reads SMTP settings
    from environment variables and defaults to a MailHog-compatible local setup
    (no authentication or TLS).
    Environment variables:
    - SMTP_HOST: SMTP server hostname (default "localhost").
    - SMTP_PORT: SMTP server port (default 1025).
    - SMTP_FROM: Sender address for the From header (default "noreply@pia.local").
    Notes:
    - Designed for local development with MailHog; production usage should enable TLS and authentication.
    - Exceptions from the underlying SMTP client are surfaced to the caller.
    """


    @staticmethod
    def send_email(email: str, subject: str, body: str) -> None:
        host = os.getenv("SMTP_HOST", "localhost")
        port = int(os.getenv("SMTP_PORT", "1025"))
        from_addr = os.getenv("SMTP_FROM", "noreply@pia.local")

        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(host, port) as smtp:
            smtp.send_message(msg)
