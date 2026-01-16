import os
import smtplib
from email.message import EmailMessage

class EmailService:


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

        # MailHog does not require auth/TLS by default
        with smtplib.SMTP(host, port) as smtp:
            smtp.send_message(msg)
