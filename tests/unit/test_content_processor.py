# ABOUTME: Test suite for ContentProcessor Hiku integration
# ABOUTME: Tests Hiku-based content extraction and conversion to article format

import pytest
from unittest.mock import Mock, patch
from pydantic import ValidationError
from yomu.content.schema import ContentFeed, ContentChannel, ContentItem
from yomu.content.processor import ContentProcessor


class TestContentProcessorHikuInitialization:
    """Test ContentProcessor Hiku extractor initialization."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.openrouter_api_key = "test-openrouter-key"
        config.cookie_file_path = "/path/to/cookies.txt"
        return config

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        db = Mock()
        return db

    def test_initialization_complete_setup(self, mock_config, mock_database):
        """Test ContentProcessor full initialization with config, extractor, and logger."""
        from yomu.content.processor import ContentProcessor

        with patch("yomu.content.processor.HikuExtractor") as mock_extractor_class:
            mock_extractor_instance = Mock()
            mock_extractor_class.return_value = mock_extractor_instance

            processor = ContentProcessor(config=mock_config, database=mock_database)

            assert processor.config == mock_config
            assert processor.hiku_extractor == mock_extractor_instance
            assert processor.logger is not None
            mock_extractor_class.assert_called_once_with(
                api_key="test-openrouter-key",
                db_path="yomu.db",
            )


class TestContentProcessorIntegration:
    """Test end-to-end integration of ContentProcessor with Hiku."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration object."""
        config = Mock()
        config.openrouter_api_key = "test-key"
        config.cookie_file_path = "/path/to/cookies.txt"
        return config

    @pytest.fixture
    def mock_database(self):
        """Mock database operations."""
        return Mock()

    def test_content_feed_to_articles_conversion(self, mock_config, mock_database):
        """Test conversion of ContentFeed to article format."""
        from yomu.content.processor import ContentProcessor

        mock_rss_feed = ContentFeed(
            channel=ContentChannel(
                title="Tech News", link="https://example.com", description="Tech news"
            ),
            items=[
                ContentItem(
                    title="AI Breakthrough",
                    link="https://example.com/ai",
                    description="Major AI development",
                    pubDate="Mon, 01 Jan 2024 10:00:00 GMT",
                ),
                ContentItem(
                    title="Cloud Computing",
                    link="https://example.com/cloud",
                    description="Cloud trends",
                    pubDate="Mon, 01 Jan 2024 11:00:00 GMT",
                ),
            ],
        )

        with patch("yomu.content.processor.HikuExtractor"):
            processor = ContentProcessor(config=mock_config, database=mock_database)

            articles = processor._content_feed_to_articles(
                mock_rss_feed, "https://example.com"
            )

            assert len(articles) == 2
            assert articles[0]["title"] == "AI Breakthrough"
            assert articles[0]["link"] == "https://example.com/ai"
            assert articles[0]["source"] == "Tech News"
            assert articles[1]["title"] == "Cloud Computing"
            assert articles[1]["link"] == "https://example.com/cloud"

    def test_conversion_with_single_item_feed(self, mock_config, mock_database):
        """Test conversion when ContentFeed has a single item."""
        from yomu.content.processor import ContentProcessor

        mock_rss_feed = ContentFeed(
            channel=ContentChannel(title="Single Item Feed"),
            items=[
                ContentItem(
                    title="Single Article",
                    link="https://example.com/article",
                    description="Article description",
                    pubDate="Mon, 01 Jan 2024 10:00:00 GMT",
                )
            ],
        )

        with patch("yomu.content.processor.HikuExtractor"):
            processor = ContentProcessor(config=mock_config, database=mock_database)
            articles = processor._content_feed_to_articles(
                mock_rss_feed, "https://example.com"
            )

            assert len(articles) == 1
            assert articles[0]["title"] == "Single Article"

    def test_process_source_propagates_hiku_errors(self, mock_config, mock_database):
        """Test that errors from Hiku propagate through process_source."""
        from yomu.content.processor import ContentProcessor

        with patch("yomu.content.processor.HikuExtractor") as mock_extractor_class:
            mock_extractor_instance = Mock()
            mock_extractor_instance.extract.side_effect = RuntimeError("Hiku failed")
            mock_extractor_class.return_value = mock_extractor_instance

            processor = ContentProcessor(config=mock_config, database=mock_database)

            with pytest.raises(RuntimeError) as exc_info:
                processor.process_source("https://example.com")

            assert "Hiku failed" in str(exc_info.value)

    def test_conversion_with_minimal_required_fields(self, mock_config, mock_database):
        """Test conversion of ContentFeed with only required fields."""
        from yomu.content.processor import ContentProcessor

        mock_rss_feed = ContentFeed(
            channel=ContentChannel(title="Minimal Feed"),
            items=[
                ContentItem(
                    title="Minimal Article",
                    link="https://example.com/minimal",
                )
            ],
        )

        with patch("yomu.content.processor.HikuExtractor"):
            processor = ContentProcessor(config=mock_config, database=mock_database)
            articles = processor._content_feed_to_articles(
                mock_rss_feed, "https://example.com"
            )

            assert len(articles) == 1
            assert articles[0]["title"] == "Minimal Article"
            assert articles[0]["link"] == "https://example.com/minimal"
            assert articles[0]["description"] == ""
            assert articles[0]["pubDate"] == ""
            assert articles[0]["source"] == "Minimal Feed"


def _create_processor():
    """Helper to create ContentProcessor with mocked HikuExtractor."""
    config = Mock()
    config.openrouter_api_key = "test-key"
    config.cookie_file_path = None
    with patch("yomu.content.processor.HikuExtractor"):
        return ContentProcessor(config=config, database=Mock())


class TestContentFeedToArticlesConversion:
    """Test conversion from ContentFeed Pydantic model to article format."""

    def test_single_item_conversion(self):
        """Test converting ContentFeed with one item to article dict."""
        feed = ContentFeed(
            channel=ContentChannel(
                title="Test Feed",
                link="https://example.com",
                description="Test Description",
            ),
            items=[
                ContentItem(
                    title="Test Article",
                    link="https://example.com/article",
                    description="Article description",
                    pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                )
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["link"] == "https://example.com/article"
        assert articles[0]["description"] == "Article description"
        assert articles[0]["pubDate"] == "Mon, 01 Jan 2024 12:00:00 GMT"
        assert articles[0]["source"] == "Test Feed"

    def test_multiple_items_conversion(self):
        """Test converting ContentFeed with multiple items."""
        feed = ContentFeed(
            channel=ContentChannel(title="Multi Feed", link="https://example.com"),
            items=[
                ContentItem(
                    title="Article 1",
                    link="https://example.com/1",
                    description="Desc 1",
                    pubDate="Mon, 01 Jan 2024 10:00:00 GMT",
                ),
                ContentItem(
                    title="Article 2",
                    link="https://example.com/2",
                    description="Desc 2",
                    pubDate="Mon, 01 Jan 2024 11:00:00 GMT",
                ),
                ContentItem(
                    title="Article 3",
                    link="https://example.com/3",
                    description="Desc 3",
                    pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                ),
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert len(articles) == 3
        assert articles[0]["title"] == "Article 1"
        assert articles[1]["title"] == "Article 2"
        assert articles[2]["title"] == "Article 3"

    def test_minimal_feed_handling(self):
        """Test handling ContentFeed with minimal data."""
        feed = ContentFeed(
            channel=ContentChannel(title="Minimal Feed"),
            items=[
                ContentItem(
                    title="Minimal Article",
                    link="https://example.com/minimal",
                )
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert len(articles) == 1
        assert isinstance(articles, list)
        assert articles[0]["title"] == "Minimal Article"

    def test_source_title_extraction(self):
        """Test extracting source from ContentChannel.title."""
        feed = ContentFeed(
            channel=ContentChannel(title="My Custom Feed Title"),
            items=[ContentItem(title="Article", link="https://example.com/article")],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert articles[0]["source"] == "My Custom Feed Title"

    def test_no_pubdate_handling(self):
        """Test that missing pubDate results in empty string."""
        feed = ContentFeed(
            channel=ContentChannel(title="Feed"),
            items=[
                ContentItem(
                    title="No Date Article",
                    link="https://example.com/nodate",
                )
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert articles[0]["pubDate"] == ""

    def test_field_mapping_completeness(self):
        """Test that all required fields map correctly."""
        feed = ContentFeed(
            channel=ContentChannel(
                title="Complete Feed",
                link="https://example.com",
                description="Feed Description",
            ),
            items=[
                ContentItem(
                    title="Complete Article",
                    link="https://example.com/complete",
                    description="Complete Description",
                    pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                )
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        article = articles[0]
        assert "title" in article
        assert "link" in article
        assert "description" in article
        assert "pubDate" in article
        assert "source" in article

    def test_minimal_required_fields_handling(self):
        """Test handling of minimal required fields (title + link only)."""
        feed = ContentFeed(
            channel=ContentChannel(title="Feed"),
            items=[
                ContentItem(
                    title="Minimal Article",
                    link="https://example.com/minimal",
                )
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert len(articles) == 1
        article = articles[0]
        assert article["title"] == "Minimal Article"
        assert article["link"] == "https://example.com/minimal"
        assert article["description"] == ""
        assert article["pubDate"] == ""

    def test_source_url_fallback_when_no_channel_title(self):
        """Test using source URL as fallback when channel title is empty."""
        source_url = "https://example.com/feed"
        feed = ContentFeed(
            channel=ContentChannel(title=""),  # Empty title
            items=[ContentItem(title="Article", link="https://example.com/article")],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, source_url)

        assert articles[0]["source"] == source_url

    def test_special_characters_in_fields(self):
        """Test handling special characters in RSS fields."""
        feed = ContentFeed(
            channel=ContentChannel(title="Feed with & Special < Characters >"),
            items=[
                ContentItem(
                    title="Title with 'quotes' and \"double quotes\"",
                    link="https://example.com/article?param=value&other=123",
                    description="Description with <html> tags & entities",
                    pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                )
            ],
        )

        processor = _create_processor()
        articles = processor._content_feed_to_articles(feed, "https://example.com")

        assert "&" in articles[0]["source"]
        assert "'" in articles[0]["title"]
        assert "&" in articles[0]["link"]
        assert "<html>" in articles[0]["description"]




class TestProcessorDelegatesValidationToHiku:
    """Test that ContentProcessor delegates all validation to Hiku."""

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

    @pytest.fixture
    def processor(self, mock_config, mock_database):
        """Create ContentProcessor instance with mocks."""
        from yomu.content.processor import ContentProcessor

        return ContentProcessor(mock_config, mock_database)

    def test_processor_propagates_hiku_validation_errors(self, processor):
        """Test that ContentProcessor propagates ValidationError from Hiku without catching it."""
        source_url = "https://example.com/invalid"

        with patch.object(processor.hiku_extractor, "extract") as mock_extract:
            mock_extract.side_effect = ValidationError.from_exception_data(
                "ContentItem validation",
                [
                    {
                        "type": "string_too_short",
                        "loc": ("items", 0, "title"),
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ],
            )

            with pytest.raises(ValidationError) as exc_info:
                processor.process_source(source_url)

            errors = exc_info.value.errors()
            assert len(errors) > 0
            assert errors[0]["type"] == "string_too_short"
