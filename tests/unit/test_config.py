# ABOUTME: Tests for unified configuration management in Yomu app
# ABOUTME: Validates YAML config loading with all API keys, newsletter settings, and validation

import pytest
import os
import tempfile
import yaml

from yomu.config.config import Config


class TestConfig:
    """Test unified configuration management."""

    def test_config_loads_all_required_fields(self):
        """Test that config loads all required fields from YAML."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss", "https://news.ycombinator.com"],
            "frequencies": ["0 9 * * *", "0 17 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = Config.load_from_file(f.name)

            assert config.openrouter_api_key == "test-api-key"
            assert config.sender_email == "test@gmail.com"
            assert config.sender_password == "test-app-password"
            assert config.recipient_email == "user@example.com"
            assert config.sources == [
                "https://example.com/rss",
                "https://news.ycombinator.com",
            ]
            assert config.frequencies == ["0 9 * * *", "0 17 * * *"]
            assert config.max_articles_per_source == 3  # Default value
            assert config.cookie_file_path == ""  # Default value
            assert config.smtp_server == "smtp.gmail.com"  # Default SMTP server
            assert config.smtp_port == 587  # Default SMTP port

        os.unlink(f.name)

    def test_config_loads_optional_fields(self):
        """Test that config loads optional fields with custom values."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
            "max_articles_per_source": 10,
            "cookie_file_path": "/path/to/cookies.txt",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = Config.load_from_file(f.name)

            assert config.max_articles_per_source == 10
            assert config.cookie_file_path == "/path/to/cookies.txt"

        os.unlink(f.name)

    def test_config_raises_error_for_missing_required_field(self):
        """Test that config raises ConfigError for missing required fields."""
        config_data = {
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(
                ValueError, match=".*required.*"
            ):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_email_format(self):
        """Test that config validates email format."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "invalid-email",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid email format"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_user_email_format(self):
        """Test that config validates user email format."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "invalid-user-email",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid email format"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_sources_list(self):
        """Test that config validates sources as a list."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": "not-a-list",
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(
                ValueError, match=".*field type.*"
            ):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_empty_sources(self):
        """Test that config validates non-empty sources list."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": [],
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match=".*empty.*"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_source_urls(self):
        """Test that config validates individual source URLs."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["invalid-url"],
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid URL"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_frequencies_list(self):
        """Test that config validates frequencies as a list."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": "not-a-list",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(
                ValueError, match=".*field type.*"
            ):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_empty_frequencies(self):
        """Test that config validates non-empty frequencies list."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match=".*empty.*"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_cron_expressions(self):
        """Test that config validates cron expression syntax."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["invalid cron"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match="Invalid cron expression"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_smtp_port_range(self):
        """Test that config validates SMTP port is within valid range."""
        # Test port too low
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
            "smtp_port": 0,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match="SMTP port must be an integer between 1 and 65535"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

        # Test port too high
        config_data["smtp_port"] = 65536

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(ValueError, match="SMTP port must be an integer between 1 and 65535"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_loads_custom_smtp_settings(self):
        """Test that config loads custom SMTP server and port values."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
            "smtp_server": "mail.example.com",
            "smtp_port": 465,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = Config.load_from_file(f.name)
            assert config.smtp_server == "mail.example.com"
            assert config.smtp_port == 465

        os.unlink(f.name)

    def test_config_file_not_found(self):
        """Test that config raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError, match="Configuration file not found"):
            Config.load_from_file("nonexistent_file.yaml")

    def test_config_invalid_yaml_syntax(self):
        """Test that config raises ValueError for invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: syntax: [")
            f.flush()

            with pytest.raises(ValueError, match="Invalid YAML syntax"):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_allows_multiple_frequencies(self):
        """Test that config supports multiple frequency schedules."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": [
                "0 9 * * *",
                "0 17 * * *",
                "0 21 * * 0",
            ],  # Multiple valid schedules
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = Config.load_from_file(f.name)
            assert len(config.frequencies) == 3
            assert "0 9 * * *" in config.frequencies
            assert "0 17 * * *" in config.frequencies
            assert "0 21 * * 0" in config.frequencies

        os.unlink(f.name)

    def test_config_loads_max_description_length_default(self):
        """Test that config loads max_description_length with default value."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = Config.load_from_file(f.name)
            assert config.max_description_length == 200  # Default value

        os.unlink(f.name)

    def test_config_loads_custom_max_description_length(self):
        """Test that config loads custom max_description_length value."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
            "max_description_length": 150,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            config = Config.load_from_file(f.name)
            assert config.max_description_length == 150

        os.unlink(f.name)

    def test_config_validates_max_description_length_type(self):
        """Test that config validates max_description_length is a positive integer."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
            "max_description_length": "not-an-integer",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(
                ValueError, match=".*positive.*"
            ):
                Config.load_from_file(f.name)

        os.unlink(f.name)

    def test_config_validates_max_description_length_positive(self):
        """Test that config validates max_description_length is positive."""
        config_data = {
            "openrouter_api_key": "test-api-key",
            "sender_email": "test@gmail.com",
            "sender_password": "test-app-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/rss"],
            "frequencies": ["0 9 * * *"],
            "max_description_length": -50,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            f.flush()

            with pytest.raises(
                ValueError, match=".*positive.*"
            ):
                Config.load_from_file(f.name)

        os.unlink(f.name)
