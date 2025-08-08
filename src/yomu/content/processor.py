# ABOUTME: Content processing pipeline delegating extraction to Hiku
# ABOUTME: Handles timestamp filtering, deduplication, and source tracking

from collections import deque
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from hikugen import HikuExtractor
from yomu.content.schema import ContentFeed
from yomu.database.database import Database
from yomu.utils import (
    get_logger,
    parse_date,
    parse_iso_timestamp,
    normalize_datetime_to_utc_naive,
)


class ContentProcessor:
    """Content processing pipeline handling both content feeds and HTML pages with LLM extraction."""

    def __init__(
        self,
        config: Any,
        database: Database,
        db_path: str = "yomu.db",
        max_fallback_urls: Optional[int] = 1000,
    ):
        """Initialize ContentProcessor with dependencies.

        Args:
            config: Configuration object with API keys
            database: Database operations instance
            db_path: Path to SQLite database file for Hikugen cache (default: yomu.db)
            max_fallback_urls: Maximum number of non-dated URLs to track (default: 1000)
        """
        self.config = config
        self.database = database
        self.hiku_extractor = HikuExtractor(
            api_key=config.openrouter_api_key,
            db_path=db_path,
        )
        self.logger = get_logger(__name__)
        self.request_timeout = 10
        self.non_dated_processed_urls = deque(maxlen=max_fallback_urls)

    def process_source(self, source_url: str) -> List[Dict[str, Any]]:
        """Process a source URL and return filtered articles.

        Args:
            source_url: URL to process

        Returns:
            List of filtered article dictionaries

        Raises:
            ValidationError: If content doesn't meet quality standards (from Hiku)
            Exception: If processing fails
        """
        self.logger.info(f"Processing source: {source_url}")

        content_feed = self.hiku_extractor.extract(
            url=source_url,
            schema=ContentFeed,
            use_cached_code=True,
            cookies_path=self.config.cookie_file_path or None,
            max_regenerate_attempts=3,
            validate_quality=True,
        )
        articles = self._content_feed_to_articles(content_feed, source_url)

        existing_source = self.database.get_source_by_url(source_url)
        last_run = (
            existing_source.get("last_successful_run") if existing_source else None
        )
        filtered_articles = self._filter_articles_by_timestamp(articles, last_run)

        self.database.add_source(source_url)
        self.database.update_source_last_run(
            source_url, datetime.now(timezone.utc).replace(tzinfo=None)
        )

        self.logger.info(f"Processed {source_url}: {len(filtered_articles)} articles")
        return filtered_articles

    def _filter_articles_by_timestamp(
        self, articles: List[Dict[str, Any]], last_run_timestamp: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Filter articles to only include those newer than last successful run.

        Args:
            articles: List of articles to filter
            last_run_timestamp: ISO timestamp of last successful run (stored as UTC naive)

        Returns:
            Filtered list of articles
        """

        last_run_utc = parse_iso_timestamp(last_run_timestamp)

        filtered_articles = []
        filtered_count = 0

        for article in articles:
            article_url = article.get("link", "")
            if article_url and article_url in self.non_dated_processed_urls:
                filtered_count += 1
                continue

            try:
                if self._should_include_article(article, last_run_utc):
                    filtered_articles.append(article)
                else:
                    filtered_count += 1
            except Exception:
                if article_url and article_url not in self.non_dated_processed_urls:
                    self.non_dated_processed_urls.append(article_url)
                filtered_articles.append(article)

        if filtered_count > 0:
            self.logger.info(
                f"Filtered {filtered_count} older articles, returning {len(filtered_articles)} new articles"
            )
        return filtered_articles

    def _should_include_article(
        self, article: Dict[str, Any], last_run_utc: Optional[datetime]
    ) -> bool:
        """Determine if article should be included after checking the deque"""

        article_url = article.get("link", "")
        pub_date_str = article.get("pubDate", "")
        article_date = parse_date(pub_date_str)

        if last_run_utc and article_date:
            return normalize_datetime_to_utc_naive(article_date) > last_run_utc.replace(
                tzinfo=None
            )

        if not article_date:
            if article_url and article_url not in self.non_dated_processed_urls:
                self.non_dated_processed_urls.append(article_url)

        return True

    def _content_feed_to_articles(
        self, content_feed: ContentFeed, source_url: str
    ) -> List[Dict[str, Any]]:
        """Convert ContentFeed Pydantic model to article format.

        Args:
            content_feed: ContentFeed model from Hiku extraction
            source_url: Original source URL

        Returns:
            List of article dictionaries in format
        """
        articles = []
        source_title = content_feed.channel.title or source_url

        for item in content_feed.items:
            article = {
                "title": item.title or "No Title",
                "link": item.link or "",
                "description": item.description or "",
                "pubDate": item.pubDate or "",
                "source": source_title,
            }
            articles.append(article)

        return articles
