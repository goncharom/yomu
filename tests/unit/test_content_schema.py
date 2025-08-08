# ABOUTME: Test suite for content schema models (ContentItem, ContentChannel, ContentFeed)
# ABOUTME: Tests Pydantic validation, field requirements, and schema integration with Hiku

import pytest
from pydantic import BaseModel, ValidationError


class TestContentItemValidation:
    """Test ContentItem Pydantic Field validation constraints."""

    def test_content_item_requires_nonempty_title(self):
        """Test that ContentItem.title requires non-empty string (min_length=1)."""
        from yomu.content.schema import ContentItem

        with pytest.raises(ValidationError) as exc_info:
            ContentItem(
                title="", link="https://example.com", description="Test", pubDate=""
            )

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("title",) for error in errors)
        assert any("at least 1 character" in str(error).lower() for error in errors)

    def test_content_item_requires_nonempty_link(self):
        """Test that ContentItem.link requires non-empty string (min_length=1)."""
        from yomu.content.schema import ContentItem

        with pytest.raises(ValidationError) as exc_info:
            ContentItem(title="Test Article", link="", description="Test", pubDate="")

        errors = exc_info.value.errors()
        assert any(error["loc"] == ("link",) for error in errors)
        assert any("at least 1 character" in str(error).lower() for error in errors)

    def test_content_item_accepts_valid_required_fields(self):
        """Test that ContentItem accepts valid non-empty title and link."""
        from yomu.content.schema import ContentItem

        item = ContentItem(
            title="Valid Article Title",
            link="https://example.com/article",
            description="Description",
            pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
        )

        assert item.title == "Valid Article Title"
        assert item.link == "https://example.com/article"

    def test_content_item_optional_fields_can_be_empty(self):
        """Test that optional fields (description, pubDate) can be empty."""
        from yomu.content.schema import ContentItem

        item = ContentItem(
            title="Article",
            link="https://example.com",
            description="",  # Optional
            pubDate="",  # Optional
        )

        assert item.title == "Article"
        assert item.link == "https://example.com"
        assert item.description == ""
        assert item.pubDate == ""

    def test_content_feed_validation_propagates_from_items(self):
        """Test that ContentFeed validation propagates ValidationError from items."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem

        channel = ContentChannel(title="Test Feed", link="https://example.com")

        with pytest.raises(ValidationError):
            ContentFeed(
                channel=channel,
                items=[
                    ContentItem(
                        title="", link="", description="", pubDate=""
                    )  # Both required fields empty
                ],
            )


class TestHikuValidationIntegration:
    """Test that Hiku extraction properly validates via Pydantic."""

    def test_hiku_adapter_propagates_pydantic_validation_errors(self):
        """Test that ContentProcessor does not catch Pydantic ValidationErrors from Hiku."""
        from yomu.content.processor import ContentProcessor
        from unittest.mock import Mock, patch

        config = Mock()
        config.openrouter_api_key = "test-key"
        config.cookie_file_path = None

        with patch("yomu.content.processor.HikuExtractor") as mock_extractor_class:
            mock_extractor = Mock()

            mock_extractor.extract.side_effect = ValidationError.from_exception_data(
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
            mock_extractor_class.return_value = mock_extractor

            processor = ContentProcessor(config=config, database=Mock())

            with pytest.raises(ValidationError) as exc_info:
                processor.process_source("https://example.com")

            errors = exc_info.value.errors()
            assert len(errors) > 0
            assert errors[0]["type"] == "string_too_short"


class TestValidationFieldDescriptions:
    """Test that schema fields have proper descriptions for Hiku."""

    def test_content_item_fields_have_descriptions(self):
        """Test that ContentItem fields have description metadata."""
        from yomu.content.schema import ContentItem

        schema = ContentItem.model_json_schema()

        assert "description" in schema["properties"]["title"]
        assert "description" in schema["properties"]["link"]
        assert "description" in schema["properties"]["description"]
        assert "description" in schema["properties"]["pubDate"]

    def test_content_channel_fields_have_descriptions(self):
        """Test that ContentChannel fields have description metadata."""
        from yomu.content.schema import ContentChannel

        schema = ContentChannel.model_json_schema()

        assert "description" in schema["properties"]["title"]
        assert "description" in schema["properties"]["link"]
        assert "description" in schema["properties"]["description"]

    def test_content_feed_has_proper_structure(self):
        """Test that ContentFeed has proper nested structure."""
        from yomu.content.schema import ContentFeed

        schema = ContentFeed.model_json_schema()

        assert "channel" in schema["properties"]
        assert "items" in schema["properties"]
        assert "description" in schema["properties"]["items"]


class TestContentItemModel:
    """Test ContentItem Pydantic model."""

    def test_rss_item_with_all_fields(self):
        """Test ContentItem accepts all valid fields."""
        from yomu.content.schema import ContentItem

        item = ContentItem(
            title="Test Article",
            link="https://example.com/article",
            description="This is a test article description",
            pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
        )

        assert item.title == "Test Article"
        assert item.link == "https://example.com/article"
        assert item.description == "This is a test article description"
        assert item.pubDate == "Mon, 01 Jan 2024 12:00:00 GMT"

    def test_rss_item_requires_title_and_link(self):
        """Test ContentItem requires title and link fields (validation enforced)."""
        from yomu.content.schema import ContentItem

        with pytest.raises(ValidationError):
            ContentItem()

        with pytest.raises(ValidationError):
            ContentItem(title="Title only")

        item = ContentItem(title="Test", link="https://example.com")
        assert item.title == "Test"
        assert item.link == "https://example.com"
        assert item.description == ""  # Optional fields still default
        assert item.pubDate == ""

    def test_rss_item_partial_fields(self):
        """Test ContentItem handles partial field specification."""
        from yomu.content.schema import ContentItem

        item = ContentItem(title="Only Title", link="https://example.com")

        assert item.title == "Only Title"
        assert item.link == "https://example.com"
        assert item.description == ""
        assert item.pubDate == ""

    def test_rss_item_is_base_model(self):
        """Test ContentItem inherits from Pydantic BaseModel."""
        from yomu.content.schema import ContentItem

        item = ContentItem(title="Test", link="https://example.com")
        assert isinstance(item, BaseModel)

    def test_rss_item_rejects_invalid_types(self):
        """Test ContentItem rejects invalid field types."""
        from yomu.content.schema import ContentItem

        with pytest.raises(ValidationError):
            ContentItem(title=123)  # title should be str, not int

    def test_rss_item_dict_conversion(self):
        """Test ContentItem can be converted to dict."""
        from yomu.content.schema import ContentItem

        item = ContentItem(
            title="Test",
            link="https://example.com",
            description="Desc",
            pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
        )

        item_dict = item.model_dump()
        assert item_dict["title"] == "Test"
        assert item_dict["link"] == "https://example.com"
        assert item_dict["description"] == "Desc"
        assert item_dict["pubDate"] == "Mon, 01 Jan 2024 12:00:00 GMT"


class TestContentChannelModel:
    """Test ContentChannel Pydantic model."""

    def test_rss_channel_with_all_fields(self):
        """Test ContentChannel accepts all valid fields."""
        from yomu.content.schema import ContentChannel

        channel = ContentChannel(
            title="Test Feed", link="https://example.com", description="A test RSS feed"
        )

        assert channel.title == "Test Feed"
        assert channel.link == "https://example.com"
        assert channel.description == "A test RSS feed"

    def test_rss_channel_with_defaults(self):
        """Test ContentChannel uses default empty strings."""
        from yomu.content.schema import ContentChannel

        channel = ContentChannel()

        assert channel.title == ""
        assert channel.link == ""
        assert channel.description == ""

    def test_rss_channel_partial_fields(self):
        """Test ContentChannel handles partial fields."""
        from yomu.content.schema import ContentChannel

        channel = ContentChannel(title="Only Title")

        assert channel.title == "Only Title"
        assert channel.link == ""
        assert channel.description == ""

    def test_rss_channel_is_base_model(self):
        """Test ContentChannel inherits from BaseModel."""
        from yomu.content.schema import ContentChannel

        channel = ContentChannel(title="Test")
        assert isinstance(channel, BaseModel)

    def test_rss_channel_rejects_invalid_types(self):
        """Test ContentChannel rejects invalid types."""
        from yomu.content.schema import ContentChannel

        with pytest.raises(ValidationError):
            ContentChannel(link=12345)  # link should be str

    def test_rss_channel_dict_conversion(self):
        """Test ContentChannel can be converted to dict."""
        from yomu.content.schema import ContentChannel

        channel = ContentChannel(
            title="Feed", link="https://example.com", description="Feed description"
        )

        channel_dict = channel.model_dump()
        assert channel_dict["title"] == "Feed"
        assert channel_dict["link"] == "https://example.com"
        assert channel_dict["description"] == "Feed description"


class TestContentFeedModel:
    """Test ContentFeed Pydantic model."""

    def test_rss_feed_with_channel_and_items(self):
        """Test ContentFeed composition with channel and items."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem

        channel = ContentChannel(
            title="Test Feed", link="https://example.com", description="Test"
        )
        items = [
            ContentItem(title="Article 1", link="https://example.com/1"),
            ContentItem(title="Article 2", link="https://example.com/2"),
        ]

        feed = ContentFeed(channel=channel, items=items)

        assert feed.channel.title == "Test Feed"
        assert len(feed.items) == 2
        assert feed.items[0].title == "Article 1"
        assert feed.items[1].title == "Article 2"

    def test_rss_feed_with_single_item(self):
        """Test ContentFeed with single item."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem

        channel = ContentChannel(title="Single Item Feed")
        item = ContentItem(title="Article", link="https://example.com/1")
        feed = ContentFeed(channel=channel, items=[item])

        assert feed.channel.title == "Single Item Feed"
        assert len(feed.items) == 1
        assert feed.items[0].title == "Article"

    def test_rss_feed_with_items_required(self):
        """Test ContentFeed requires at least one item to be valid."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem
        from pydantic import ValidationError

        channel = ContentChannel(title="Feed")

        # Explicitly passing empty items should fail validation
        with pytest.raises(ValidationError):
            ContentFeed(channel=channel, items=[])

    def test_rss_feed_is_base_model(self):
        """Test ContentFeed inherits from BaseModel."""
        from yomu.content.schema import ContentFeed, ContentChannel

        feed = ContentFeed(channel=ContentChannel(title="Test"))
        assert isinstance(feed, BaseModel)

    def test_rss_feed_nested_validation(self):
        """Test ContentFeed validates nested models."""
        from yomu.content.schema import ContentFeed

        with pytest.raises(ValidationError):
            ContentFeed(channel="not a channel object", items=[])

    def test_rss_feed_dict_conversion(self):
        """Test ContentFeed can be converted to dict."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem

        channel = ContentChannel(title="Feed", link="https://example.com")
        items = [ContentItem(title="Article", link="https://example.com/1")]
        feed = ContentFeed(channel=channel, items=items)

        feed_dict = feed.model_dump()
        assert feed_dict["channel"]["title"] == "Feed"
        assert len(feed_dict["items"]) == 1
        assert feed_dict["items"][0]["title"] == "Article"

    def test_rss_feed_with_multiple_items(self):
        """Test ContentFeed handles multiple items correctly."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem

        channel = ContentChannel(title="Multi-Item Feed")
        items = [
            ContentItem(
                title=f"Article {i}",
                link=f"https://example.com/{i}",
                description=f"Description {i}",
                pubDate=f"Mon, {i:02d} Jan 2024 12:00:00 GMT",
            )
            for i in range(1, 6)
        ]

        feed = ContentFeed(channel=channel, items=items)

        assert len(feed.items) == 5
        for i, item in enumerate(feed.items, start=1):
            assert item.title == f"Article {i}"
            assert item.link == f"https://example.com/{i}"


class TestSchemaIntegration:
    """Test schema integration with Hiku patterns and real-world usage."""

    def test_schema_json_schema_generation(self):
        """Test that schema can generate JSON schema (required for Hiku)."""
        from yomu.content.schema import ContentFeed

        schema_json = ContentFeed.model_json_schema()

        assert "properties" in schema_json
        assert "channel" in schema_json["properties"]
        assert "items" in schema_json["properties"]

    def test_model_validate_from_dict(self):
        """Test ContentFeed.model_validate() works with dict (Hiku returns dicts)."""
        from yomu.content.schema import ContentFeed

        data = {
            "channel": {
                "title": "Test Feed",
                "link": "https://example.com",
                "description": "Test",
            },
            "items": [
                {
                    "title": "Article 1",
                    "link": "https://example.com/1",
                    "description": "Desc 1",
                    "pubDate": "Mon, 01 Jan 2024 12:00:00 GMT",
                }
            ],
        }

        feed = ContentFeed.model_validate(data)

        assert feed.channel.title == "Test Feed"
        assert len(feed.items) == 1
        assert feed.items[0].title == "Article 1"

    def test_model_validate_with_missing_optional_fields(self):
        """Test model_validate handles missing optional fields gracefully."""
        from yomu.content.schema import ContentFeed

        data = {
            "channel": {"title": "Feed"},
            "items": [
                {
                    "title": "Article",
                    "link": "https://example.com/article",  # Required field
                }
            ],
        }

        feed = ContentFeed.model_validate(data)

        assert feed.channel.title == "Feed"
        assert feed.channel.link == ""
        assert feed.channel.description == ""
        assert feed.items[0].title == "Article"
        assert feed.items[0].link == "https://example.com/article"
        assert feed.items[0].description == ""
        assert feed.items[0].pubDate == ""

    def test_real_rss_like_data_structure(self):
        """Test with realistic RSS-like data."""
        from yomu.content.schema import ContentFeed

        data = {
            "channel": {
                "title": "Tech News Daily",
                "link": "https://technews.example.com",
                "description": "Latest technology news and updates",
            },
            "items": [
                {
                    "title": "AI Breakthrough: New Model Announced",
                    "link": "https://technews.example.com/ai-breakthrough",
                    "description": "A major AI research lab has announced a groundbreaking new model...",
                    "pubDate": "Thu, 10 Oct 2024 14:30:00 GMT",
                },
                {
                    "title": "Cloud Computing Trends 2024",
                    "link": "https://technews.example.com/cloud-trends",
                    "description": "Industry experts discuss the future of cloud infrastructure...",
                    "pubDate": "Thu, 10 Oct 2024 10:15:00 GMT",
                },
            ],
        }

        feed = ContentFeed.model_validate(data)

        assert feed.channel.title == "Tech News Daily"
        assert len(feed.items) == 2
        assert "AI Breakthrough" in feed.items[0].title
        assert "Cloud Computing" in feed.items[1].title

    def test_schema_hash_consistency(self):
        """Test that schema produces consistent JSON for hashing."""
        from yomu.content.schema import ContentFeed
        import json

        schema1 = json.dumps(ContentFeed.model_json_schema(), sort_keys=True)
        schema2 = json.dumps(ContentFeed.model_json_schema(), sort_keys=True)

        assert schema1 == schema2

    def test_model_instantiation_directly(self):
        """Test direct model instantiation works (alternative to model_validate)."""
        from yomu.content.schema import ContentFeed, ContentChannel, ContentItem

        feed = ContentFeed(
            channel=ContentChannel(
                title="Direct Feed",
                link="https://example.com",
                description="Created directly",
            ),
            items=[
                ContentItem(
                    title="Direct Article",
                    link="https://example.com/article",
                    description="Direct description",
                    pubDate="Mon, 01 Jan 2024 12:00:00 GMT",
                )
            ],
        )

        assert feed.channel.title == "Direct Feed"
        assert len(feed.items) == 1
        assert feed.items[0].title == "Direct Article"

    def test_empty_items_fails_validation(self):
        """Test that empty items list fails validation."""
        from yomu.content.schema import ContentFeed
        from pydantic import ValidationError

        data = {
            "channel": {
                "title": "Empty Feed",
                "link": "https://example.com",
                "description": "No articles yet",
            },
            "items": [],
        }

        with pytest.raises(ValidationError):
            ContentFeed.model_validate(data)
