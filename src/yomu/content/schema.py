# ABOUTME: Pydantic schema for content feed extraction
# ABOUTME: Defines structure for Hiku-based content code generation

from pydantic import BaseModel, Field
from typing import List


class ContentItem(BaseModel):
    """Single content feed item with validation."""

    title: str = Field(min_length=1, description="Article title (required)")
    link: str = Field(
        min_length=1, description="Article URL (required, must be full path)"
    )
    description: str = Field(
        default="",
        description="Article description or, if missing, any additional data (eg: number of upvotes/comments) (required)",
    )
    pubDate: str = Field(
        default="",
        description="Publication date",
    )


class ContentChannel(BaseModel):
    """Content channel metadata."""

    title: str = Field(default="", description="Feed title")
    link: str = Field(default="", description="Feed URL")
    description: str = Field(default="", description="Feed description")


class ContentFeed(BaseModel):
    """Complete content feed structure."""

    channel: ContentChannel = Field(description="Content channel metadata")
    items: List[ContentItem] = Field(
        default_factory=list,
        min_length=1,
        description="List of content items. Focus on articles, news, posts and other things of the sort. Ignore other elements",
    )
