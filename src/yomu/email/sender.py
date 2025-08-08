# ABOUTME: SMTP email sending functionality for Yomu newsletter app
# ABOUTME: Implements EmailSender class for sending HTML newsletters via configurable SMTP

import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Any


class EmailSender:
    """SMTP email sender for HTML newsletter distribution."""

    def __init__(self, config: Any):
        """Initialize EmailSender with configuration.

        Args:
            config: Configuration object with sender_email, sender_password, smtp_server, and smtp_port
        """
        self.sender_email = config.sender_email
        self.sender_password = config.sender_password
        self.smtp_server = config.smtp_server
        self.smtp_port = config.smtp_port

    def send_email(self, to_email: str, subject: str, body: str):
        """Send HTML email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body: HTML email body content

        Raises:
            ValueError: If input validation fails
            EmailError: If SMTP operation fails
        """
        # Create email message
        message = MIMEText(body, "html", "utf-8")
        message["From"] = self.sender_email
        message["To"] = to_email
        message["Subject"] = subject
        message["Date"] = formatdate(localtime=True)
        message["Message-ID"] = make_msgid()

        # Send via SMTP
        server = None
        try:
            # Connect to SMTP server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)

            # Send message
            server.send_message(message)
        finally:
            if server:
                server.quit()
