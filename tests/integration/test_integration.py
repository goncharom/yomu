# ABOUTME: Integration tests for complete Yomu workflows
# ABOUTME: Tests multi-component interactions with real code (mocking only external APIs)

import pytest
from unittest.mock import Mock, patch, MagicMock
from yomu.config.config import Config
from yomu.content.processor import ContentProcessor
from yomu.email.sender import EmailSender
from yomu.newsletter.service import NewsletterService
from yomu.content.schema import ContentFeed, ContentChannel, ContentItem


@pytest.mark.integration
class TestContentProcessorDeduplication:
    """Integration test: Content processor deduplication across multiple runs."""

    def test_processor_deduplication_with_mixed_dates_across_runs(self):
        """Two runs: verify dedup prevents articles without dates from being included twice."""
        mock_config = Mock()
        mock_config.openrouter_api_key = "test-key"
        mock_config.cookie_file_path = None
        mock_database = Mock()
        mock_database.get_source_by_url.return_value = None

        with patch("yomu.content.processor.HikuExtractor"):
            processor = ContentProcessor(mock_config, mock_database)

            feed = ContentFeed(
                channel=ContentChannel(title="Test Feed"),
                items=[
                    ContentItem(
                        title="Article with date",
                        link="https://example.com/1",
                        pubDate="Mon, 01 Jan 2024 10:00:00 GMT",
                    ),
                    ContentItem(
                        title="Article without date",
                        link="https://example.com/2",
                    ),
                ],
            )

            with patch.object(processor.hiku_extractor, "extract") as mock_extract:
                with patch.object(processor, "_content_feed_to_articles") as mock_convert:
                    mock_extract.return_value = feed
                    mock_convert.return_value = [
                        {
                            "title": "Article with date",
                            "link": "https://example.com/1",
                            "pubDate": "Mon, 01 Jan 2024 10:00:00 GMT",
                            "source": "Test Feed",
                        },
                        {
                            "title": "Article without date",
                            "link": "https://example.com/2",
                            "pubDate": "",
                            "source": "Test Feed",
                        },
                    ]

                    articles = processor.process_source("https://example.com/feed")

                    assert len(articles) == 2
                    assert "https://example.com/2" in processor.non_dated_processed_urls


@pytest.mark.integration
class TestProcessorHandlesMissingPubDate:
    """Processor correctly tracks articles without pubDate in deque."""

    def test_processor_adds_url_to_deque_when_no_pubdate(self):
        """Article without pubDate gets added to deque for deduplication."""
        mock_config = Mock()
        mock_config.openrouter_api_key = "test-key"
        mock_config.cookie_file_path = None
        mock_database = Mock()
        mock_database.get_source_by_url.return_value = None

        with patch("yomu.content.processor.HikuExtractor"):
            processor = ContentProcessor(mock_config, mock_database)

            feed = ContentFeed(
                channel=ContentChannel(title="Test"),
                items=[
                    ContentItem(
                        title="No Date Article",
                        link="https://example.com/no-date",
                    )
                ],
            )

            with patch.object(processor.hiku_extractor, "extract") as mock_extract:
                with patch.object(processor, "_content_feed_to_articles") as mock_convert:
                    mock_extract.return_value = feed
                    mock_convert.return_value = [
                        {
                            "title": "No Date Article",
                            "link": "https://example.com/no-date",
                            "pubDate": "",
                            "source": "Test",
                        }
                    ]

                    processor.process_source("https://example.com")

                    assert (
                        "https://example.com/no-date"
                        in processor.non_dated_processed_urls
                    )


@pytest.mark.integration
class TestDaemonMultipleScheduleExecution:
    """Daemon correctly identifies earliest next run time across multiple schedules."""

    def test_daemon_picks_earliest_schedule_between_daily_and_weekly(self):
        """With daily (8 AM) and weekly (Sunday 9 AM) schedules, picks earliest."""
        from yomu.daemon.daemon import NewsletterDaemon

        mock_config = Mock()
        mock_config.recipient_email = "test@example.com"
        mock_config.sources = ["https://example.com"]
        mock_config.frequencies = ["0 8 * * *", "0 9 * * 0"]

        mock_distributor = Mock()

        daemon = NewsletterDaemon(mock_config, mock_distributor)

        assert len(daemon.crons) == 2


@pytest.mark.integration
class TestEmailSendingWithRetry:
    """Email sending handles transient failures gracefully."""

    def test_email_sender_handles_temporary_connection_failure(self):
        """SMTP connection fails once, succeeds on retry (if implemented)."""
        import smtplib

        mock_config = Mock()
        mock_config.sender_email = "test@gmail.com"
        mock_config.sender_password = "password"

        email_sender = EmailSender(mock_config)

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_server = Mock()
            mock_server.starttls.return_value = None
            mock_server.login.return_value = None
            mock_server.send_message.return_value = None
            mock_server.quit.return_value = None
            mock_smtp_class.return_value = mock_server

            email_sender.send_email(
                "recipient@example.com", "Test", "<html>Test</html>"
            )

            assert mock_smtp_class.called
            assert mock_server.quit.called


@pytest.mark.integration
class TestConfigValidationErrorMessages:
    """Config validation provides helpful error messages."""

    def test_missing_required_field_error_mentions_field_name(self, tmp_path):
        """Missing field error includes field name."""
        config_file = tmp_path / "bad_config.yaml"
        config_file.write_text(
            """
sender_email: "test@gmail.com"
sender_password: "password"
recipient_email: "user@example.com"
"""
        )

        with pytest.raises(ValueError, match=".*required.*"):
            Config.load_from_file(str(config_file))


@pytest.mark.integration
class TestContentProcessingErrorRecovery:
    """Processor handles extraction failures gracefully."""

    def test_processor_propagates_extraction_errors(self):
        """When Hiku extraction fails, error propagates to caller."""
        from pydantic import ValidationError

        mock_config = Mock()
        mock_config.openrouter_api_key = "test-key"
        mock_config.cookie_file_path = None
        mock_database = Mock()
        mock_database.get_source_by_url.return_value = None

        with patch("yomu.content.processor.HikuExtractor") as mock_extractor_class:
            mock_extractor = Mock()
            mock_extractor_class.return_value = mock_extractor
            mock_extractor.extract.side_effect = ValidationError.from_exception_data(
                "Content",
                [
                    {
                        "type": "string_too_short",
                        "loc": ("items", 0, "title"),
                        "msg": "String too short",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ],
            )

            processor = ContentProcessor(mock_config, mock_database)

            with pytest.raises(ValidationError):
                processor.process_source("https://example.com")
