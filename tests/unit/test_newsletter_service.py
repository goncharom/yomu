# ABOUTME: Tests for NewsletterService combining generation and distribution
# ABOUTME: Validates the unified newsletter workflow from source processing to email delivery

from unittest.mock import Mock

from yomu.newsletter.service import NewsletterService
from yomu.config.config import Config


class TestNewsletterService:
    """Test NewsletterService functionality."""

    def setup_method(self):
        """Set up test dependencies."""
        self.config = Config(
            openrouter_api_key="test-key",
            sender_email="sender@gmail.com",
            sender_password="test-password",
            recipient_email="test@example.com",
            sources=["https://example.com/rss"],
            frequencies=["0 9 * * *"],
            max_articles_per_source=3,
        )
        self.source_processor = Mock()
        self.email_sender = Mock()
        self.newsletter_service = NewsletterService(
            self.config, self.source_processor, self.email_sender
        )

    def test_send_newsletter_to_user_success(self):
        """Test successful newsletter sending."""
        mock_articles = [{"title": "Test", "source": "Test Source"}]
        self.source_processor.process_source.return_value = mock_articles
        self.email_sender.send_email.return_value = None  # Success

        result = self.newsletter_service.send_newsletter_to_user(
            "test@example.com", ["https://example.com"]
        )

        assert result is True
        self.source_processor.process_source.assert_called_once()
        self.email_sender.send_email.assert_called_once()

        call_args = self.email_sender.send_email.call_args[0]
        assert call_args[0] == "test@example.com"
        assert "Your Newsletter" in call_args[1]  # Subject
        assert isinstance(call_args[2], str)  # HTML content

    def test_send_newsletter_to_user_empty_sources(self):
        """Test sending newsletter with no sources returns False."""
        result = self.newsletter_service.send_newsletter_to_user("test@example.com", [])

        assert result is False
        self.source_processor.process_source.assert_not_called()
        self.email_sender.send_email.assert_not_called()

    def test_send_newsletter_to_user_generation_failure(self):
        """Test handling of newsletter generation failure."""
        self.source_processor.process_source.side_effect = Exception(
            "Generation failed"
        )

        result = self.newsletter_service.send_newsletter_to_user(
            "test@example.com", ["https://example.com"]
        )

        assert result is False
        self.email_sender.send_email.assert_not_called()

    def test_send_newsletter_to_user_email_failure(self):
        """Test handling of email sending failure."""
        mock_articles = [{"title": "Test", "source": "Test Source"}]
        self.source_processor.process_source.return_value = mock_articles
        self.email_sender.send_email.side_effect = Exception("Email failed")

        result = self.newsletter_service.send_newsletter_to_user(
            "test@example.com", ["https://example.com"]
        )

        assert result is False
        self.source_processor.process_source.assert_called_once()
        self.email_sender.send_email.assert_called_once()

    def test_send_newsletter_to_user_empty_content(self):
        """Test handling when no content is generated."""
        self.source_processor.process_source.return_value = []

        result = self.newsletter_service.send_newsletter_to_user(
            "test@example.com", ["https://example.com"]
        )

        assert result is False
        self.email_sender.send_email.assert_not_called()

    def test_send_newsletter_to_user_applies_max_articles_limit(self):
        """Test that max_articles_per_source limit is applied correctly."""
        articles = [
            {
                "title": f"Article {i}",
                "link": f"http://example.com/{i}",
                "description": f"Description {i}",
                "pubDate": "2024-01-01T10:00:00Z",
                "source": "Test Source",
            }
            for i in range(10)  # 10 articles, limit is 3
        ]
        self.source_processor.process_source.return_value = articles

        self.newsletter_service.html_template.generate_newsletter = Mock(
            return_value="<html>Newsletter</html>"
        )

        result = self.newsletter_service.send_newsletter_to_user(
            "test@example.com", ["https://example.com/rss"]
        )

        assert result is True

        self.newsletter_service.html_template.generate_newsletter.assert_called_once()
        call_args = self.newsletter_service.html_template.generate_newsletter.call_args[
            0
        ][0]

        assert "Test Source" in call_args
        assert (
            len(call_args["Test Source"]["articles"]) == 3
        )  # Limited to max_articles_per_source

        self.email_sender.send_email.assert_called_once()

    def test_send_newsletter_to_user_preserves_source_urls(self):
        """Test that send_newsletter_to_user preserves source URLs in articles_by_source structure."""
        mock_articles = [
            {
                "title": "Test Article",
                "link": "https://example.com/article",
                "description": "Test description",
                "source": "Hacker News",
            }
        ]
        self.source_processor.process_source.return_value = mock_articles

        self.newsletter_service.html_template.generate_newsletter = Mock(
            return_value="<html>Newsletter</html>"
        )

        self.newsletter_service.send_newsletter_to_user(
            "test@example.com", ["https://news.ycombinator.com"]
        )

        self.newsletter_service.html_template.generate_newsletter.assert_called_once()
        call_args = self.newsletter_service.html_template.generate_newsletter.call_args[
            0
        ][0]

        assert "Hacker News" in call_args
        assert isinstance(call_args["Hacker News"], dict)
        assert "url" in call_args["Hacker News"]
        assert "articles" in call_args["Hacker News"]
        assert call_args["Hacker News"]["url"] == "https://news.ycombinator.com"
        assert len(call_args["Hacker News"]["articles"]) == 1

    def test_send_newsletter_preserves_urls_with_multiple_sources(self):
        """Test that URL preservation works with multiple sources."""
        mock_articles_1 = [{"title": "Article 1", "source": "Source One"}]
        mock_articles_2 = [{"title": "Article 2", "source": "Source Two"}]

        def mock_process_source(url):
            if url == "https://source1.com":
                return mock_articles_1
            elif url == "https://source2.com":
                return mock_articles_2
            return []

        self.source_processor.process_source.side_effect = mock_process_source
        self.newsletter_service.html_template.generate_newsletter = Mock(
            return_value="<html>Newsletter</html>"
        )

        self.newsletter_service.send_newsletter_to_user(
            "test@example.com",
            ["https://source1.com", "https://source2.com"],
        )

        call_args = self.newsletter_service.html_template.generate_newsletter.call_args[
            0
        ][0]

        assert "Source One" in call_args
        assert call_args["Source One"]["url"] == "https://source1.com"
        assert call_args["Source One"]["articles"] == mock_articles_1

        assert "Source Two" in call_args
        assert call_args["Source Two"]["url"] == "https://source2.com"
        assert call_args["Source Two"]["articles"] == mock_articles_2


class TestNewsletterServiceIntegration:
    """Integration tests for NewsletterService."""

    def test_service_can_be_imported_from_service_module(self):
        """Test that NewsletterService can be imported from the service module."""
        from yomu.newsletter.service import NewsletterService as ImportedService

        assert ImportedService is not None
        assert ImportedService == NewsletterService

    def test_service_maintains_all_required_methods(self):
        """Test that NewsletterService has all required methods."""
        config = Config(
            openrouter_api_key="test-key",
            sender_email="sender@gmail.com",
            sender_password="test-password",
            recipient_email="test@example.com",
            sources=["https://example.com/rss"],
            frequencies=["0 9 * * *"],
            max_articles_per_source=3,
        )
        source_processor = Mock()
        email_sender = Mock()
        service = NewsletterService(config, source_processor, email_sender)

        assert callable(service.send_newsletter_to_user)
