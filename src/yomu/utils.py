# ABOUTME: Consolidated utilities module for Yomu app
# ABOUTME: Contains logging, exceptions, date parsing, and text processing utilities

import logging
import sys
from datetime import datetime, timezone
from typing import Optional


def setup_logger(name: str = "yomu", level: int = logging.INFO) -> logging.Logger:
    """Set up logger with console output.

    Args:
            name: Logger name
            level: Logging level

    Returns:
            Configured logger
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get logger instance.

    Args:
            name: Logger name, defaults to calling module

    Returns:
            Logger instance
    """
    if name is None:
        name = "yomu"
    return logging.getLogger(name)


COMMON_DATE_FORMATS = [
    "%a, %d %b %Y %H:%M:%S %Z",
    "%a, %d %b %Y %H:%M:%S %z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d %H:%M:%S",
]


def _parse_date_string(date_str: str) -> Optional[datetime]:
    """Parse date string using common formats.

    Helper function that extracts common parsing logic for date functions.
    Attempts standard formats then falls back to ISO parsing.

    Args:
            date_str: Cleaned date string (non-empty, stripped whitespace)

    Returns:
            Parsed datetime object, or None if parsing fails
    """
    for fmt in COMMON_DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_iso_timestamp(timestamp_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO format timestamp (from database storage).

    Parses timestamps stored in the database which are always in ISO format
    without timezone info. Assumes UTC.

    Args:
            timestamp_str: ISO format timestamp string (can be None)

    Returns:
            Datetime object with UTC timezone, or None if parsing fails
    """
    if not timestamp_str:
        return None

    try:
        return datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
    except (ValueError, AttributeError):
        return None


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse publication date from various formats.

    Attempts to parse common date formats including RFC 822 and ISO 8601.
    Handles both RSS and other content feed formats.

    Args:
            date_str: Date string from content feed (can be None)

    Returns:
            Parsed datetime object, or None if parsing fails
    """
    if date_str is None or not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()
    return _parse_date_string(date_str)


def format_readable_date(date_str: Optional[str]) -> Optional[str]:
    """Format date for newsletter display in human-readable format.

    Parses various date formats and formats them as "Month DD, YYYY at HH:MM AM/PM".
    Works with RSS, Atom, and other content feed date formats.

    Args:
            date_str: Date string from content feed (can be None)

    Returns:
            Formatted date string, or None if parsing fails
    """
    if date_str is None or not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()
    parsed_date = _parse_date_string(date_str)
    if parsed_date is None:
        return None

    return parsed_date.strftime("%B %d, %Y at %I:%M %p")


def normalize_datetime_to_utc_naive(dt: datetime) -> datetime:
    """Convert datetime to UTC timezone-naive for consistent comparison.

    Handles both timezone-aware and timezone-naive datetime objects.
    Timezone-aware datetimes are converted to UTC then made naive.
    Timezone-naive datetimes are assumed to already be in UTC.

    Args:
            dt: Datetime object (timezone-aware or naive)

    Returns:
            UTC timezone-naive datetime
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    else:
        return dt


def truncate_description(text: str, max_length: int) -> str:
    """Truncate description text to specified length with smart word boundary handling.

    Args:
            text: The text to truncate (can be None)
            max_length: Maximum character length (including ellipsis)

    Returns:
            Truncated text with ellipsis if needed, or original text if under limit
    """
    if not text:
        return ""

    if max_length <= 0:
        return ""

    if len(text) <= max_length:
        return text

    ellipsis = "..."
    if max_length <= 3:
        return ellipsis[:max_length] if max_length > 0 else ""

    available_length = max_length - len(ellipsis)

    truncated = text[:available_length]

    last_space = truncated.rfind(" ")

    if last_space > 0:
        truncated = truncated[:last_space]

    if len(truncated) == 0:
        truncated = text[:available_length]

    return truncated + ellipsis
