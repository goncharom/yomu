# ABOUTME: Test suite for SMTP email sending functionality
# ABOUTME: Tests EmailSender class with mocked SMTP server interactions

import pytest
from unittest.mock import Mock, patch
import smtplib
from yomu.email.sender import EmailSender


@pytest.fixture
def mock_config():
    """Mock configuration with sender credentials and SMTP settings."""
    config = Mock()
    config.sender_email = "test@gmail.com"
    config.sender_password = "testpassword123"
    config.smtp_server = "smtp.gmail.com"
    config.smtp_port = 587
    return config


@pytest.fixture
def email_sender(mock_config):
    """Create EmailSender instance with mock config."""
    return EmailSender(mock_config)


class TestEmailSending:
    """Test email sending functionality."""

    @patch("smtplib.SMTP")
    def test_send_email_success(self, mock_smtp_class, email_sender):
        """Test successful email sending."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server

        to_email = "recipient@example.com"
        subject = "Test Subject"
        body = "<html><body><h1>Test HTML message</h1></body></html>"

        email_sender.send_email(to_email, subject, body)

        mock_smtp_class.assert_called_once_with("smtp.gmail.com", 587)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@gmail.com", "testpassword123")
        mock_server.send_message.assert_called_once()
        mock_server.quit.assert_called_once()

        sent_message = mock_server.send_message.call_args[0][0]
        assert sent_message["From"] == "test@gmail.com"
        assert sent_message["To"] == to_email
        assert sent_message["Subject"] == subject
        assert body in sent_message.get_payload(decode=True).decode("utf-8")

    @patch("smtplib.SMTP")
    def test_send_email_authentication_failure(self, mock_smtp_class, email_sender):
        """Test email sending with authentication failure."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )

        with pytest.raises(Exception) as exc_info:
            email_sender.send_email("test@example.com", "Subject", "Body")

        assert "Authentication failed" in str(exc_info.value)

    @patch("smtplib.SMTP")
    def test_send_email_connection_failure(self, mock_smtp_class, email_sender):
        """Test email sending with connection failure."""
        mock_smtp_class.side_effect = smtplib.SMTPConnectError(
            421, "Service not available"
        )

        with pytest.raises(Exception) as exc_info:
            email_sender.send_email("test@example.com", "Subject", "Body")

        assert "Service not available" in str(exc_info.value)

    @patch("smtplib.SMTP")
    def test_send_email_recipient_failure(self, mock_smtp_class, email_sender):
        """Test email sending with recipient error."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused(
            {"test@example.com": (550, "User unknown")}
        )

        with pytest.raises(Exception) as exc_info:
            email_sender.send_email("test@example.com", "Subject", "Body")

        assert "User unknown" in str(exc_info.value)

    @patch("smtplib.SMTP")
    def test_send_email_server_cleanup_on_error(self, mock_smtp_class, email_sender):
        """Test that SMTP server is properly cleaned up on errors."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Auth failed"
        )

        with pytest.raises(Exception):
            email_sender.send_email("test@example.com", "Subject", "Body")

        mock_server.quit.assert_called_once()


class TestEmailFormatting:
    """Test email message formatting."""

    @patch("smtplib.SMTP")
    def test_email_headers_formatting(self, mock_smtp_class, email_sender):
        """Test that email headers are properly formatted."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server

        to_email = "recipient@example.com"
        subject = "Test Subject with Special Characters: àéîöü"
        body = "Body with unicode: 📧 ✉️"

        email_sender.send_email(to_email, subject, body)

        sent_message = mock_server.send_message.call_args[0][0]
        assert sent_message["From"] == "test@gmail.com"
        assert sent_message["To"] == to_email
        assert sent_message["Subject"] == subject
        assert "Date" in sent_message
        assert "Message-ID" in sent_message

    @patch("smtplib.SMTP")
    def test_email_body_encoding(self, mock_smtp_class, email_sender):
        """Test that email body handles unicode correctly."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server

        unicode_body = "Unicode test: 你好世界 🌍"

        email_sender.send_email("test@example.com", "Subject", unicode_body)

        sent_message = mock_server.send_message.call_args[0][0]
        assert unicode_body in sent_message.get_payload(decode=True).decode("utf-8")

    @patch("smtplib.SMTP")
    def test_multiline_body_formatting(self, mock_smtp_class, email_sender):
        """Test that multiline email bodies are handled correctly."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server

        multiline_body = """Line 1
Line 2
Line 3 with special chars: àéîöü"""

        email_sender.send_email("test@example.com", "Subject", multiline_body)

        sent_message = mock_server.send_message.call_args[0][0]
        body_content = sent_message.get_payload(decode=True).decode("utf-8")
        assert "Line 1" in body_content
        assert "Line 2" in body_content
        assert "Line 3 with special chars: àéîöü" in body_content

    @patch("smtplib.SMTP")
    def test_html_email_content_type(self, mock_smtp_class, email_sender):
        """Test that emails are sent as HTML content type."""
        mock_server = Mock()
        mock_smtp_class.return_value = mock_server

        html_body = "<html><body><h1>HTML Newsletter</h1><p>Content</p></body></html>"
        email_sender.send_email("test@example.com", "HTML Newsletter", html_body)

        sent_message = mock_server.send_message.call_args[0][0]
        assert sent_message.get_content_type() == "text/html"
        assert html_body in sent_message.get_payload(decode=True).decode("utf-8")
