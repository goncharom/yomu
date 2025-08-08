# ABOUTME: Newsletter service combining generation and email distribution
# ABOUTME: Handles complete newsletter workflow from source processing to email delivery

from typing import List
from datetime import datetime
from yomu.content.processor import ContentProcessor
from yomu.email.templates import HTMLTemplate
from yomu.email.sender import EmailSender
from yomu.config.config import Config
from yomu.utils import get_logger


class NewsletterService:
    """Newsletter service combining generation and email distribution."""

    def __init__(
        self,
        config: Config,
        content_processor: ContentProcessor,
        email_sender: EmailSender,
    ):
        """Initialize NewsletterService with dependencies.

        Args:
            config: Unified configuration with max_articles_per_source setting
            content_processor: Content processor for fetching articles (contains database access)
            email_sender: Email sender for delivering newsletters
        """
        self.config = config
        self.content_processor = content_processor
        self.email_sender = email_sender
        self.html_template = HTMLTemplate(config)
        self.logger = get_logger(__name__)

    def send_newsletter_to_user(self, user_email: str, sources: List[str]) -> bool:
        """Send newsletter to a specific user with provided sources.

        Args:
            user_email: User's email address
            sources: List of source URLs to generate newsletter from

        Returns:
            True if newsletter was sent successfully, False otherwise
        """
        if not sources:
            self.logger.info(f"No sources provided for user {user_email}")
            return False

        articles_by_source = self._collect_articles_from_sources(sources)

        if not articles_by_source:
            self.logger.info(f"No articles found for user {user_email}")
            return False

        try:
            newsletter_content = self.html_template.generate_newsletter(
                articles_by_source
            )
        except Exception as e:
            self.logger.error(f"Failed to generate newsletter for {user_email}: {e}")
            return False

        try:
            subject = f"Your Newsletter - {datetime.now().strftime('%B %d, %Y')}"
            self.email_sender.send_email(user_email, subject, newsletter_content)
            self.logger.info(f"Newsletter sent successfully to {user_email}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send newsletter to {user_email}: {e}")
            return False

    def _collect_articles_from_sources(self, sources: List[str]) -> dict:
        """Collect articles from multiple sources with per-source article limit applied.

        Args:
            sources: List of source URLs to process

        Returns:
            Dictionary mapping source names to article data with URL preserved
        """
        articles_by_source = {}

        if not sources:
            self.logger.info("No sources provided")

        for source_url in sources:
            try:
                articles = self.content_processor.process_source(source_url)
                if articles:
                    original_count = len(articles)

                    articles = articles[: self.config.max_articles_per_source]
                    if original_count > self.config.max_articles_per_source:
                        source_name = articles[0].get("source", source_url)
                        self.logger.info(
                            f"Limited {source_name}: {original_count} articles → {len(articles)} articles (max_articles_per_source={self.config.max_articles_per_source})"
                        )

                    source_name = articles[0].get("source", source_url)
                    articles_by_source[source_name] = {
                        "url": source_url,
                        "articles": articles,
                    }
            except Exception as e:
                self.logger.warning(f"Failed to process source {source_url}: {e}")
                continue

        return articles_by_source
