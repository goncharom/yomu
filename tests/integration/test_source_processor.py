# ABOUTME: Test suite for content feed processing pipeline integration
# ABOUTME: Tests ContentProcessor class using Hiku for extraction

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from collections import deque
from yomu.content.processor import ContentProcessor
from yomu.content.schema import ContentFeed, ContentChannel, ContentItem


@pytest.mark.integration
class TestContentProcessor:
    """Test ContentProcessor class functionality."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.openrouter_api_key = "test-key"
        config.cookie_file_path = None
        return config

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        db = Mock()
        db.get_source_by_url.return_value = None  # No existing source by default
        return db

    @pytest.fixture
    def processor(self, mock_config, mock_database):
        """Create ContentProcessor instance with mocks."""
        return ContentProcessor(mock_config, mock_database)

    def test_process_source_with_existing_rss_feed(self, processor, mock_database):
        """Test processing a source that already has RSS."""
        source_url = "https://example.com/feed.xml"

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed", link=source_url, description="Test Feed"
                ),
                items=[
                    ContentItem(
                        title="Test Article 1",
                        link="https://example.com/article1",
                        description="First test article",
                        pubDate="Sun, 01 Jan 2023 10:00:00 GMT",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Test Article 1",
                    "link": "https://example.com/article1",
                    "description": "First test article",
                    "pubDate": "Sun, 01 Jan 2023 10:00:00 GMT",
                    "source": "Test Feed",
                }
            ]

            articles = processor.process_source(source_url)

            assert len(articles) == 1
            assert articles[0]["title"] == "Test Article 1"
            assert articles[0]["link"] == "https://example.com/article1"
            mock_extract.assert_called_once()
            call_kwargs = mock_extract.call_args[1]
            assert call_kwargs["url"] == source_url
            assert call_kwargs["schema"] == ContentFeed
            mock_convert.assert_called_once_with(mock_rss_feed, source_url)

    def test_process_source_with_html_page_first_time(self, processor, mock_database):
        """Test processing a non-RSS page using Hiku."""
        source_url = "https://example.com/blog"

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test", link="https://example.com", description="Test"
                ),
                items=[
                    ContentItem(
                        title="Test Article",
                        link="https://example.com/test",
                        description="Test",
                        pubDate="Mon, 01 Jan 2024 10:00:00 GMT",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Test Article",
                    "link": "https://example.com/test",
                    "description": "Test",
                    "pubDate": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "source": "Test",
                }
            ]

            articles = processor.process_source(source_url)

            mock_extract.assert_called_once()
            call_kwargs = mock_extract.call_args[1]
            assert call_kwargs["url"] == source_url
            assert call_kwargs["schema"] == ContentFeed
            mock_convert.assert_called_once_with(mock_rss_feed, source_url)
            mock_database.add_source.assert_called_once_with(source_url)
            assert len(articles) == 1
            assert articles[0]["title"] == "Test Article"

    def test_article_filtering_by_timestamp(self, processor, mock_database):
        """Test that articles are filtered by last successful run timestamp."""
        source_url = "https://example.com/feed.xml"
        last_run = datetime(2023, 1, 1, 12, 0, 0)

        mock_source = {
            "url": source_url,
            "extraction_code": None,
            "last_successful_run": last_run.isoformat(),
        }

        mock_database.get_source_by_url.return_value = mock_source

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed", link=source_url, description="Test Feed"
                ),
                items=[
                    ContentItem(
                        title="Old Article",
                        link="https://example.com/old",
                        description="Before last run",
                        pubDate="Sun, 01 Jan 2023 10:00:00 GMT",
                    ),
                    ContentItem(
                        title="New Article",
                        link="https://example.com/new",
                        description="After last run",
                        pubDate="Sun, 01 Jan 2023 14:00:00 GMT",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Old Article",
                    "link": "https://example.com/old",
                    "description": "Before last run",
                    "pubDate": "Sun, 01 Jan 2023 10:00:00 GMT",
                    "source": "Test Feed",
                },
                {
                    "title": "New Article",
                    "link": "https://example.com/new",
                    "description": "After last run",
                    "pubDate": "Sun, 01 Jan 2023 14:00:00 GMT",
                    "source": "Test Feed",
                },
            ]

            articles = processor.process_source(source_url)

            assert len(articles) == 1
            assert articles[0]["title"] == "New Article"

    def test_network_error_handling(self, processor, mock_database):
        """Test handling of network errors when fetching source."""
        source_url = "https://example.com/unreachable"

        with patch.object(processor.hiku_extractor, "extract") as mock_extract:
            import requests

            mock_extract.side_effect = requests.exceptions.ConnectionError(
                "Network error"
            )

            with pytest.raises(Exception):
                processor.process_source(source_url)

    def test_invalid_rss_handling(self, processor, mock_database):
        """Test handling of invalid RSS content with Hiku."""
        source_url = "https://example.com/bad-rss"

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Generated",
                    link="https://example.com",
                    description="Generated",
                ),
                items=[
                    ContentItem(
                        title="Generated Article",
                        link="https://example.com/generated",
                        description="Generated",
                        pubDate="Mon, 01 Jan 2024 10:00:00 GMT",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Generated Article",
                    "link": "https://example.com/generated",
                    "description": "Generated",
                    "pubDate": "Mon, 01 Jan 2024 10:00:00 GMT",
                    "source": "Generated",
                }
            ]

            articles = processor.process_source(source_url)

            mock_extract.assert_called_once()
            call_kwargs = mock_extract.call_args[1]
            assert call_kwargs["url"] == source_url
            assert call_kwargs["schema"] == ContentFeed
            assert len(articles) == 1
            assert articles[0]["title"] == "Generated Article"


@pytest.mark.integration
class TestContentProcessorDequeIntegration:
    """Test ContentProcessor deque integration for non-dated URL tracking."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.openrouter_api_key = "test-key"
        config.cookie_file_path = None
        return config

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        db = Mock()
        db.get_source_by_url.return_value = None
        return db

    def test_processor_initializes_with_empty_deque(self, mock_config, mock_database):
        """Test ContentProcessor initializes with empty non_dated_processed_urls deque."""
        processor = ContentProcessor(mock_config, mock_database)

        assert hasattr(processor, "non_dated_processed_urls")

        assert isinstance(processor.non_dated_processed_urls, deque)

        assert len(processor.non_dated_processed_urls) == 0

    def test_processor_initializes_with_configurable_maxlen(
        self, mock_config, mock_database
    ):
        """Test ContentProcessor accepts configurable maxlen for deque."""
        processor = ContentProcessor(mock_config, mock_database, max_fallback_urls=500)

        assert processor.non_dated_processed_urls.maxlen == 500

    def test_processor_uses_default_maxlen_when_none_provided(
        self, mock_config, mock_database
    ):
        """Test ContentProcessor uses default maxlen when none provided."""
        processor = ContentProcessor(mock_config, mock_database)

        assert processor.non_dated_processed_urls.maxlen == 1000

    def test_url_stored_when_rss_has_no_pubdate_element(
        self, mock_config, mock_database
    ):
        """Test URL stored when RSS item has no pubDate element."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="Article Without Date",
                        link="https://example.com/no-date",
                        description="This article has no pubDate",
                        pubDate="",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Article Without Date",
                    "link": "https://example.com/no-date",
                    "description": "This article has no pubDate",
                    "pubDate": "",
                    "source": "Test Feed",
                }
            ]

            processor.process_source("https://example.com/feed")

            assert "https://example.com/no-date" in processor.non_dated_processed_urls
            assert len(processor.non_dated_processed_urls) == 1

    def test_url_stored_when_pubdate_content_unparseable(
        self, mock_config, mock_database
    ):
        """Test URL stored when pubDate content cannot be parsed."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="Article With Bad Date",
                        link="https://example.com/bad-date",
                        description="This article has unparseable date",
                        pubDate="invalid-date-format",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Article With Bad Date",
                    "link": "https://example.com/bad-date",
                    "description": "This article has unparseable date",
                    "pubDate": "invalid-date-format",
                    "source": "Test Feed",
                }
            ]

            processor.process_source("https://example.com/feed")

            assert "https://example.com/bad-date" in processor.non_dated_processed_urls
            assert len(processor.non_dated_processed_urls) == 1

    def test_url_not_stored_when_pubdate_parses_successfully(
        self, mock_config, mock_database
    ):
        """Test URL NOT stored when pubDate parses successfully."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="Article With Good Date",
                        link="https://example.com/good-date",
                        description="This article has valid date",
                        pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Article With Good Date",
                    "link": "https://example.com/good-date",
                    "description": "This article has valid date",
                    "pubDate": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "source": "Test Feed",
                }
            ]

            processor.process_source("https://example.com/feed")

            assert (
                "https://example.com/good-date"
                not in processor.non_dated_processed_urls
            )
            assert len(processor.non_dated_processed_urls) == 0

    def test_correct_article_url_stored_from_link_element(
        self, mock_config, mock_database
    ):
        """Test correct article URL is stored from link element."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="First Article",
                        link="https://example.com/first",
                        description="First article without date",
                        pubDate="",
                    ),
                    ContentItem(
                        title="Second Article",
                        link="https://example.com/second",
                        description="Second article with date",
                        pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                    ),
                    ContentItem(
                        title="Third Article",
                        link="https://example.com/third",
                        description="Third article without date",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "First Article",
                    "link": "https://example.com/first",
                    "description": "First article without date",
                    "pubDate": "",
                    "source": "Test Feed",
                },
                {
                    "title": "Second Article",
                    "link": "https://example.com/second",
                    "description": "Second article with date",
                    "pubDate": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "source": "Test Feed",
                },
                {
                    "title": "Third Article",
                    "link": "https://example.com/third",
                    "description": "Third article without date",
                    "pubDate": "",
                    "source": "Test Feed",
                },
            ]

            processor.process_source("https://example.com/feed")

            assert "https://example.com/first" in processor.non_dated_processed_urls
            assert "https://example.com/third" in processor.non_dated_processed_urls

            assert (
                "https://example.com/second" not in processor.non_dated_processed_urls
            )

            assert len(processor.non_dated_processed_urls) == 2


@pytest.mark.integration
class TestContentProcessorDeduplication:
    """Test ContentProcessor deduplication filtering logic."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.openrouter_api_key = "test-key"
        config.cookie_file_path = None
        return config

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        db = Mock()
        db.get_source_by_url.return_value = None
        return db

    def test_articles_filtered_when_url_exists_in_deque(
        self, mock_config, mock_database
    ):
        """Test articles filtered when their URL exists in deque."""
        processor = ContentProcessor(mock_config, mock_database)

        processor.non_dated_processed_urls.append(
            "https://example.com/already-processed"
        )

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="Already Processed Article",
                        link="https://example.com/already-processed",
                        description="This article was already processed",
                        pubDate="",
                    ),
                    ContentItem(
                        title="New Article",
                        link="https://example.com/new-article",
                        description="This is a new article",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Already Processed Article",
                    "link": "https://example.com/already-processed",
                    "description": "This article was already processed",
                    "pubDate": "",
                    "source": "Test Feed",
                },
                {
                    "title": "New Article",
                    "link": "https://example.com/new-article",
                    "description": "This is a new article",
                    "pubDate": "",
                    "source": "Test Feed",
                },
            ]

            articles = processor.process_source("https://example.com/feed")

            article_links = [article["link"] for article in articles]
            assert "https://example.com/already-processed" not in article_links
            assert "https://example.com/new-article" in article_links
            assert len(articles) == 1

    def test_articles_pass_when_url_not_in_deque(self, mock_config, mock_database):
        """Test articles pass filtering when URL not in deque."""
        processor = ContentProcessor(mock_config, mock_database)

        processor.non_dated_processed_urls.append("https://other.com/other-article")

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="New Article 1",
                        link="https://example.com/new1",
                        description="First new article",
                        pubDate="",
                    ),
                    ContentItem(
                        title="New Article 2",
                        link="https://example.com/new2",
                        description="Second new article",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "New Article 1",
                    "link": "https://example.com/new1",
                    "description": "First new article",
                    "pubDate": "",
                    "source": "Test Feed",
                },
                {
                    "title": "New Article 2",
                    "link": "https://example.com/new2",
                    "description": "Second new article",
                    "pubDate": "",
                    "source": "Test Feed",
                },
            ]

            articles = processor.process_source("https://example.com/feed")

            article_links = [article["link"] for article in articles]
            assert "https://example.com/new1" in article_links
            assert "https://example.com/new2" in article_links
            assert len(articles) == 2

    def test_filtering_works_with_existing_timestamp_logic(
        self, mock_config, mock_database
    ):
        """Test URL filtering works correctly with existing timestamp logic."""
        processor = ContentProcessor(mock_config, mock_database)

        last_run = datetime(2024, 1, 1, 12, 0, 0)
        mock_source = {
            "url": "https://example.com/feed",
            "extraction_code": None,
            "last_successful_run": last_run.isoformat(),
        }
        mock_database.get_source_by_url.return_value = mock_source

        processor.non_dated_processed_urls.append("https://example.com/duplicate")

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="Old Article",
                        link="https://example.com/old",
                        description="Article before last run",
                        pubDate="Sun, 31 Dec 2023 10:00:00 GMT",
                    ),
                    ContentItem(
                        title="New Article",
                        link="https://example.com/new",
                        description="Article after last run",
                        pubDate="Mon, 02 Jan 2024 10:00:00 GMT",
                    ),
                    ContentItem(
                        title="Duplicate Article",
                        link="https://example.com/duplicate",
                        description="Duplicate with no date",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Old Article",
                    "link": "https://example.com/old",
                    "description": "Article before last run",
                    "pubDate": "Sun, 31 Dec 2023 10:00:00 GMT",
                    "source": "Test Feed",
                },
                {
                    "title": "New Article",
                    "link": "https://example.com/new",
                    "description": "Article after last run",
                    "pubDate": "Mon, 02 Jan 2024 10:00:00 GMT",
                    "source": "Test Feed",
                },
                {
                    "title": "Duplicate Article",
                    "link": "https://example.com/duplicate",
                    "description": "Duplicate with no date",
                    "pubDate": "",
                    "source": "Test Feed",
                },
            ]

            articles = processor.process_source("https://example.com/feed")

            article_links = [article["link"] for article in articles]
            assert (
                "https://example.com/old" not in article_links
            )  # Filtered by timestamp
            assert "https://example.com/new" in article_links  # Passes both filters
            assert (
                "https://example.com/duplicate" not in article_links
            )  # Filtered by URL
            assert len(articles) == 1

    def test_filtering_uses_article_link_field_for_comparison(
        self, mock_config, mock_database
    ):
        """Test filtering uses article's link field for URL comparison."""
        processor = ContentProcessor(mock_config, mock_database)

        target_url = "https://example.com/target-article"
        processor.non_dated_processed_urls.append(target_url)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Test Feed",
                    link="https://example.com/feed",
                    description="Test Feed",
                ),
                items=[
                    ContentItem(
                        title="Target Article",
                        link=target_url,
                        description="This article should be filtered",
                        pubDate="",
                    ),
                    ContentItem(
                        title="Other Article",
                        link="https://example.com/other",
                        description="This article should pass",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Target Article",
                    "link": target_url,
                    "description": "This article should be filtered",
                    "pubDate": "",
                    "source": "Test Feed",
                },
                {
                    "title": "Other Article",
                    "link": "https://example.com/other",
                    "description": "This article should pass",
                    "pubDate": "",
                    "source": "Test Feed",
                },
            ]

            articles = processor.process_source("https://example.com/feed")

            article_links = [article["link"] for article in articles]
            assert target_url not in article_links
            assert "https://example.com/other" in article_links
            assert len(articles) == 1


@pytest.mark.integration
class TestEndToEndDuplicatePrevention:
    """Test end-to-end duplicate prevention for the original problem scenario."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.openrouter_api_key = "test-key"
        config.cookie_file_path = None
        return config

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        db = Mock()
        db.get_source_by_url.return_value = None
        return db

    def test_consecutive_runs_with_fallback_dates_prevents_duplicates(
        self, mock_config, mock_database
    ):
        """Test the original duplicate problem: consecutive runs with articles that fall back to current date."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Problematic Feed",
                    link="https://example.com/feed",
                    description="Problematic Feed",
                ),
                items=[
                    ContentItem(
                        title="Article Without Date 1",
                        link="https://example.com/article1",
                        description="This article has no date and would cause duplicates",
                        pubDate="",
                    ),
                    ContentItem(
                        title="Article Without Date 2",
                        link="https://example.com/article2",
                        description="This article also has no date",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Article Without Date 1",
                    "link": "https://example.com/article1",
                    "description": "This article has no date and would cause duplicates",
                    "pubDate": "",
                    "source": "Problematic Feed",
                },
                {
                    "title": "Article Without Date 2",
                    "link": "https://example.com/article2",
                    "description": "This article also has no date",
                    "pubDate": "",
                    "source": "Problematic Feed",
                },
            ]

            first_run_articles = processor.process_source("https://example.com/feed")

            first_run_links = [article["link"] for article in first_run_articles]
            assert "https://example.com/article1" in first_run_links
            assert "https://example.com/article2" in first_run_links
            assert len(first_run_articles) == 2

            assert "https://example.com/article1" in processor.non_dated_processed_urls
            assert "https://example.com/article2" in processor.non_dated_processed_urls

            second_run_articles = processor.process_source("https://example.com/feed")

            assert len(second_run_articles) == 0

    def test_mixed_articles_with_and_without_dates(self, mock_config, mock_database):
        """Test mixed scenario: some articles with dates, some without."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Mixed Feed",
                    link="https://example.com/feed",
                    description="Mixed Feed",
                ),
                items=[
                    ContentItem(
                        title="Article With Date",
                        link="https://example.com/dated",
                        description="This article has a proper date",
                        pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                    ),
                    ContentItem(
                        title="Article Without Date",
                        link="https://example.com/undated",
                        description="This article has no date",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": "Article With Date",
                    "link": "https://example.com/dated",
                    "description": "This article has a proper date",
                    "pubDate": "Mon, 01 Jan 2024 12:00:00 GMT",
                    "source": "Mixed Feed",
                },
                {
                    "title": "Article Without Date",
                    "link": "https://example.com/undated",
                    "description": "This article has no date",
                    "pubDate": "",
                    "source": "Mixed Feed",
                },
            ]

            first_run_articles = processor.process_source("https://example.com/feed")

            first_run_links = [article["link"] for article in first_run_articles]
            assert "https://example.com/dated" in first_run_links
            assert "https://example.com/undated" in first_run_links
            assert len(first_run_articles) == 2

            assert "https://example.com/undated" in processor.non_dated_processed_urls
            assert "https://example.com/dated" not in processor.non_dated_processed_urls

            second_run_articles = processor.process_source("https://example.com/feed")

            second_run_links = [article["link"] for article in second_run_articles]
            assert "https://example.com/dated" in second_run_links
            assert "https://example.com/undated" not in second_run_links
            assert len(second_run_articles) == 1

    def test_new_articles_after_duplicates_are_tracked(
        self, mock_config, mock_database
    ):
        """Test that new articles are included even after duplicates are tracked."""
        processor = ContentProcessor(mock_config, mock_database)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed_1 = ContentFeed(
                channel=ContentChannel(
                    title="Growing Feed",
                    link="https://example.com/feed",
                    description="Growing Feed",
                ),
                items=[
                    ContentItem(
                        title="Original Article",
                        link="https://example.com/original",
                        description="First article without date",
                        pubDate="",
                    )
                ],
            )
            mock_extract.return_value = mock_rss_feed_1
            mock_convert.return_value = [
                {
                    "title": "Original Article",
                    "link": "https://example.com/original",
                    "description": "First article without date",
                    "pubDate": "",
                    "source": "Growing Feed",
                }
            ]

            first_run_articles = processor.process_source("https://example.com/feed")
            assert len(first_run_articles) == 1
            assert "https://example.com/original" in processor.non_dated_processed_urls

            mock_rss_feed_2 = ContentFeed(
                channel=ContentChannel(
                    title="Growing Feed",
                    link="https://example.com/feed",
                    description="Growing Feed",
                ),
                items=[
                    ContentItem(
                        title="Original Article",
                        link="https://example.com/original",
                        description="First article without date",
                        pubDate="",
                    ),
                    ContentItem(
                        title="New Article",
                        link="https://example.com/new",
                        description="New article without date",
                        pubDate="",
                    ),
                ],
            )
            mock_extract.return_value = mock_rss_feed_2
            mock_convert.return_value = [
                {
                    "title": "Original Article",
                    "link": "https://example.com/original",
                    "description": "First article without date",
                    "pubDate": "",
                    "source": "Growing Feed",
                },
                {
                    "title": "New Article",
                    "link": "https://example.com/new",
                    "description": "New article without date",
                    "pubDate": "",
                    "source": "Growing Feed",
                },
            ]

            second_run_articles = processor.process_source("https://example.com/feed")

            second_run_links = [article["link"] for article in second_run_articles]
            assert (
                "https://example.com/original" not in second_run_links
            )  # Filtered as duplicate
            assert "https://example.com/new" in second_run_links  # New article included
            assert len(second_run_articles) == 1

            assert "https://example.com/original" in processor.non_dated_processed_urls
            assert "https://example.com/new" in processor.non_dated_processed_urls

    def test_deque_bounded_behavior_with_many_articles(
        self, mock_config, mock_database
    ):
        """Test that deque properly handles bounds when many articles are processed."""
        processor = ContentProcessor(mock_config, mock_database, max_fallback_urls=3)

        with (
            patch.object(processor.hiku_extractor, "extract") as mock_extract,
            patch.object(processor, "_content_feed_to_articles") as mock_convert,
        ):
            mock_rss_feed = ContentFeed(
                channel=ContentChannel(
                    title="Large Feed",
                    link="https://example.com/feed",
                    description="Large Feed",
                ),
                items=[
                    ContentItem(
                        title=f"Article {i}",
                        link=f"https://example.com/article{i}",
                        description=f"Article {i}",
                        pubDate="",
                    )
                    for i in range(1, 6)
                ],
            )
            mock_extract.return_value = mock_rss_feed
            mock_convert.return_value = [
                {
                    "title": f"Article {i}",
                    "link": f"https://example.com/article{i}",
                    "description": f"Article {i}",
                    "pubDate": "",
                    "source": "Large Feed",
                }
                for i in range(1, 6)
            ]

            articles = processor.process_source("https://example.com/feed")

            assert len(articles) == 5

            assert len(processor.non_dated_processed_urls) == 3

            deque_urls = list(processor.non_dated_processed_urls)
            assert "https://example.com/article3" in deque_urls
            assert "https://example.com/article4" in deque_urls
            assert "https://example.com/article5" in deque_urls

            assert "https://example.com/article1" not in deque_urls
            assert "https://example.com/article2" not in deque_urls
