# ABOUTME: Unified YAML configuration management for Yomu newsletter app
# ABOUTME: Combines API keys, SMTP settings, newsletter sources and scheduling in single config.yaml

import os
import re
import yaml
from dataclasses import dataclass
from typing import List
from urllib.parse import urlparse
from croniter import croniter
from datetime import datetime


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


@dataclass
class Config:
    """Unified configuration for Yomu application loaded from YAML."""

    # API Configuration
    openrouter_api_key: str
    sender_email: str
    sender_password: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    cookie_file_path: str = ""

    # Newsletter Configuration
    recipient_email: str = ""
    sources: List[str] = None
    frequencies: List[str] = None
    max_articles_per_source: int = 3
    max_description_length: int = 200

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.sources is None:
            self.sources = []
        if self.frequencies is None:
            self.frequencies = []

    @classmethod
    def load_from_file(cls, config_path: str) -> "Config":
        """Load configuration from YAML file with validation."""
        data = cls._load_yaml_data(config_path)
        cls._validate_required_fields(data)
        cls._validate_field_types(data)
        cls._validate_optional_fields(data)

        config = cls(
            openrouter_api_key=data["openrouter_api_key"],
            sender_email=data["sender_email"],
            sender_password=data["sender_password"],
            smtp_server=data.get("smtp_server", "smtp.gmail.com"),
            smtp_port=data.get("smtp_port", 587),
            cookie_file_path=data.get("cookie_file_path", ""),
            recipient_email=data["recipient_email"],
            sources=data["sources"],
            frequencies=data["frequencies"],
            max_articles_per_source=data.get("max_articles_per_source", 3),
            max_description_length=data.get("max_description_length", 200),
        )

        config.validate()
        return config

    @staticmethod
    def _load_yaml_data(config_path: str) -> dict:
        """Load YAML data from file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError("Configuration file not found")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")

    @staticmethod
    def _validate_required_fields(data: dict) -> None:
        """Validate that all required fields are present."""
        required_fields = [
            "openrouter_api_key",
            "sender_email",
            "sender_password",
            "recipient_email",
            "sources",
            "frequencies",
        ]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

    @staticmethod
    def _validate_field_types(data: dict) -> None:
        """Validate that field types are correct."""
        if not isinstance(data["sources"], list):
            raise ValueError("Invalid field type: sources must be a list")

        if not isinstance(data["frequencies"], list):
            raise ValueError("Invalid field type: frequencies must be a list")

    @staticmethod
    def _validate_optional_fields(data: dict) -> None:
        """Validate optional fields if present."""
        if "max_description_length" not in data:
            return

        if not isinstance(data["max_description_length"], int):
            raise ValueError("max_description_length must be a positive integer")
        if data["max_description_length"] <= 0:
            raise ValueError("max_description_length must be a positive integer")

    def validate(self) -> None:
        """Validate configuration values."""
        # Validate API keys
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key cannot be empty")
        if not self.sender_password:
            raise ValueError("Sender password cannot be empty")

        # Validate SMTP settings
        if not self.smtp_server:
            raise ValueError("SMTP server cannot be empty")
        if not isinstance(self.smtp_port, int) or self.smtp_port < 1 or self.smtp_port > 65535:
            raise ValueError("SMTP port must be an integer between 1 and 65535")

        # Validate email fields
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not self.sender_email:
            raise ValueError("Sender email cannot be empty")
        if not re.match(email_pattern, self.sender_email):
            raise ValueError("Invalid email format")
        if not self.recipient_email:
            raise ValueError("Recipient email cannot be empty")
        if not re.match(email_pattern, self.recipient_email):
            raise ValueError("Invalid email format")

        # Validate sources and frequencies
        self._validate_sources()
        self._validate_frequencies()

        # Validate max_description_length
        if not isinstance(self.max_description_length, int):
            raise ValueError("max_description_length must be a positive integer")
        if self.max_description_length <= 0:
            raise ValueError("max_description_length must be a positive integer")

    def _validate_sources(self) -> None:
        """Validate sources list."""
        if not self.sources:
            raise ValueError("Sources list cannot be empty")

        for source_url in self.sources:
            self._validate_url(source_url)

    def _validate_url(self, url: str) -> None:
        """Validate individual URL."""
        if not url:
            raise ValueError("Invalid URL")

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL")

        if parsed.scheme not in ("http", "https"):
            raise ValueError("Invalid URL")

    def _validate_frequencies(self) -> None:
        """Validate frequencies field as valid cron expressions."""
        if not self.frequencies:
            raise ValueError("Frequencies cannot be empty")

        if not isinstance(self.frequencies, list):
            raise ValueError("Frequencies must be a list")

        # Validate each cron expression
        for frequency in self.frequencies:
            if not frequency:
                raise ValueError("Frequency cannot be empty")

            # Validate cron expression syntax
            try:
                croniter(frequency, datetime.now())
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid cron expression: {e}")

            # Cron expression syntax is valid
