# ABOUTME: Test suite for main application entry point with YAML config integration
# ABOUTME: Tests CLI parsing, YAML config loading, and application component initialization

import pytest
import tempfile
import os
import sys
import yaml
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from main import main, create_app_components, parse_arguments, initialize_database
from yomu.config.config import Config


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_parse_arguments_default_values(self):
        """Test default argument values."""
        args = parse_arguments([])

        assert not hasattr(args, "config")
        assert args.config_file == "config.yaml"  # New default config file
        assert args.db_path == "yomu.db"
        assert args.log_level == "INFO"
        assert not args.init_db

    def test_parse_arguments_custom_values(self):
        """Test custom argument values."""
        test_args = [
            "--config-file",
            "/custom/config.yaml",
            "--db-path",
            "/custom/yomu.db",
            "--log-level",
            "DEBUG",
            "--init-db",
        ]

        args = parse_arguments(test_args)

        assert args.config_file == "/custom/config.yaml"
        assert args.db_path == "/custom/yomu.db"
        assert args.log_level == "DEBUG"
        assert args.init_db

    def test_parse_arguments_config_file_only(self):
        """Test parsing with only config file argument."""
        test_args = ["--config-file", "/path/to/newsletter.yaml"]

        args = parse_arguments(test_args)

        assert args.config_file == "/path/to/newsletter.yaml"


class TestDatabaseInitialization:
    """Test database initialization functionality."""

    @patch("main.Database")
    def test_initialize_database_success(self, mock_database_class):
        """Test successful database initialization."""
        mock_db = Mock()
        mock_database_class.return_value.__enter__.return_value = mock_db

        initialize_database("test.db")

        mock_database_class.assert_called_once_with("test.db")
        mock_db.create_tables.assert_called_once()

    @patch("main.Database")
    def test_initialize_database_existing_file(self, mock_database_class):
        """Test initialization with existing database file."""
        mock_db = Mock()
        mock_database_class.return_value.__enter__.return_value = mock_db

        initialize_database("existing.db")

        mock_database_class.assert_called_once_with("existing.db")
        mock_db.create_tables.assert_called_once()


class TestYAMLConfigIntegration:
    """Test YAML configuration loading and integration."""

    @pytest.fixture
    def sample_yaml_config(self):
        """Sample YAML configuration content."""
        return {
            "openrouter_api_key": "test-api-key",
            "sender_email": "sender@gmail.com",
            "sender_password": "test-password",
            "recipient_email": "user@example.com",
            "sources": ["https://example.com/feed1", "https://example.com/feed2"],
            "frequencies": ["0 9 * * *"],  # Daily at 9 AM
            "max_articles_per_source": 3,
        }

    @pytest.fixture
    def mock_env_config(self):
        """Mock environment configuration."""
        config = Mock()
        config.openrouter_api_key = "test-api-key"
        config.sender_email = "test@gmail.com"
        config.sender_password = "test-password"
        return config

    def test_config_file_loading_success(self, sample_yaml_config):
        """Test successful YAML config file loading."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            yaml.dump(sample_yaml_config, temp_file)
            config_path = temp_file.name

        try:
            from yomu.config.config import Config

            config = Config.load_from_file(config_path)

            assert config.recipient_email == "user@example.com"
            assert len(config.sources) == 2
            assert config.frequencies == ["0 9 * * *"]

        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)

    def test_config_file_missing_error(self):
        """Test error handling for missing config file."""
        from yomu.config.config import Config

        with pytest.raises(Exception):  # Should raise appropriate exception
            Config.load_from_file("/nonexistent/config.yaml")

    def test_config_file_invalid_yaml_error(self):
        """Test error handling for invalid YAML syntax."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as temp_file:
            temp_file.write("invalid: yaml: content: [")  # Invalid YAML
            config_path = temp_file.name

        try:
            from yomu.config.config import Config

            with pytest.raises(Exception):  # Should raise YAML parsing exception
                Config.load_from_file(config_path)

        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)


class TestAppComponentCreation:
    """Test application component creation with YAML config integration."""

    @pytest.fixture
    def mock_env_config(self):
        """Mock environment configuration (no IMAP needed)."""
        config = Mock()
        config.openrouter_api_key = "test-api-key"
        config.sender_email = "test@gmail.com"
        config.sender_password = "test-password"
        return config

    @pytest.fixture
    def mock_yaml_config(self):
        """Mock YAML configuration."""
        from yomu.config.config import Config

        return Config(
            openrouter_api_key="test-key",
            sender_email="sender@gmail.com",
            sender_password="test-password",
            recipient_email="test@example.com",
            sources=["https://example.com/feed1", "https://example.com/feed2"],
            frequencies=["0 9 * * *"],
            max_articles_per_source=3,
        )

    @patch("main.Database")
    @patch("main.EmailSender")
    @patch("main.ContentProcessor")
    @patch("main.NewsletterService")
    @patch("main.NewsletterDaemon")
    def test_create_app_components_single_user_architecture(
        self,
        mock_daemon_class,
        mock_newsletter_class,
        mock_processor_class,
        mock_sender_class,
        mock_db_class,
        mock_env_config,
        mock_yaml_config,
    ):
        """Test creation of application components."""
        mock_db = Mock()
        mock_sender = Mock()
        mock_processor = Mock()
        mock_newsletter = Mock()
        mock_daemon = Mock()

        mock_db_class.return_value = mock_db
        mock_sender_class.return_value = mock_sender
        mock_processor_class.return_value = mock_processor
        mock_newsletter_class.return_value = mock_newsletter
        mock_daemon_class.return_value = mock_daemon

        unified_config = Config(
            openrouter_api_key="test-key",
            sender_email="sender@gmail.com",
            sender_password="test-password",
            recipient_email="user@example.com",
            sources=["https://example.com/rss"],
            frequencies=["0 9 * * *"],
            max_articles_per_source=3,
        )
        components = create_app_components(unified_config, "test.db")

        assert "database" in components
        assert "email_sender" in components  # Still needed to SEND newsletters
        assert "content_processor" in components
        assert (
            "newsletter_service" in components
        )  # Consolidated from generator + distributor
        assert "daemon" in components

        assert "email_receiver" not in components
        assert "subscription_manager" not in components

        mock_db_class.assert_called_once_with("test.db")
        mock_sender_class.assert_called_once_with(unified_config)
        mock_processor_class.assert_called_once_with(unified_config, mock_db, "test.db")
        mock_newsletter_class.assert_called_once_with(
            unified_config, mock_processor, mock_sender
        )
        mock_daemon_class.assert_called_once_with(unified_config, mock_newsletter)


class TestMainFunction:
    """Test main function execution with YAML config integration."""

    @pytest.fixture
    def sample_yaml_config(self):
        """Sample YAML configuration for testing."""
        return {
            "openrouter_api_key": "test-api-key",
            "sender_email": "sender@gmail.com",
            "sender_password": "test-password",
            "recipient_email": "test@example.com",
            "sources": ["https://example.com/feed"],
            "frequencies": ["0 9 * * *"],
            "max_articles_per_source": 3,
        }

    @patch("yomu.config.config.Config.load_from_file")
    @patch("main.initialize_database")
    def test_main_with_init_db_only(self, mock_init_db, mock_get_config):
        """Test main function with database initialization only."""
        mock_config = Mock()
        mock_get_config.return_value = mock_config

        test_args = ["--init-db", "--db-path", "test.db"]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        mock_init_db.assert_called_once_with("test.db")

        assert result == 0

    @patch("yomu.config.config.Config.load_from_file")
    @patch("main.create_app_components")
    def test_main_with_yaml_config_loading(
        self,
        mock_create_components,
        mock_load_from_file,
        sample_yaml_config,
    ):
        """Test main function with YAML configuration loading."""
        mock_unified_config = Config(**sample_yaml_config)
        mock_load_from_file.return_value = mock_unified_config

        mock_daemon = Mock()
        mock_components = {"daemon": mock_daemon}
        mock_create_components.return_value = mock_components

        test_args = ["--config-file", "test-config.yaml", "--db-path", "test.db"]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        mock_load_from_file.assert_called_once_with("test-config.yaml")

        mock_create_components.assert_called_once_with(mock_unified_config, "test.db")

        mock_daemon.run.assert_called_once()

        assert result == 0

    @patch("yomu.config.config.Config.load_from_file")
    @patch("yomu.config.config.Config.load_from_file")
    def test_main_yaml_config_file_missing(self, mock_load_yaml, mock_get_config):
        """Test main function with missing YAML config file."""
        mock_get_config.return_value = Mock()
        mock_load_yaml.side_effect = FileNotFoundError("Config file not found")

        test_args = ["--config-file", "missing.yaml"]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        assert result == 1

    @patch("yomu.config.config.Config.load_from_file")
    @patch("yomu.config.config.Config.load_from_file")
    def test_main_yaml_config_invalid(self, mock_load_yaml, mock_get_config):
        """Test main function with invalid YAML config."""
        mock_get_config.return_value = Mock()
        mock_load_yaml.side_effect = Exception("Invalid YAML configuration")

        test_args = ["--config-file", "invalid.yaml"]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        assert result == 1

    @patch("yomu.config.config.Config.load_from_file")
    def test_main_env_config_error(self, mock_get_config):
        """Test main function with environment configuration error."""
        mock_get_config.side_effect = Exception("Missing required environment variable")

        with patch("sys.argv", ["main.py"]):
            result = main()

        assert result == 1

    @patch("yomu.config.config.Config.load_from_file")
    @patch("main.create_app_components")
    def test_main_daemon_error(
        self,
        mock_create_components,
        mock_load_from_file,
        sample_yaml_config,
    ):
        """Test main function with daemon error."""
        mock_unified_config = Config(**sample_yaml_config)
        mock_load_from_file.return_value = mock_unified_config

        mock_daemon = Mock()
        mock_daemon.run.side_effect = Exception("Daemon startup failed")
        mock_components = {"daemon": mock_daemon}
        mock_create_components.return_value = mock_components

        with patch("sys.argv", ["main.py"]):
            result = main()

        assert result == 1

    @patch("yomu.config.config.Config.load_from_file")
    @patch("main.create_app_components")
    def test_main_keyboard_interrupt(
        self,
        mock_create_components,
        mock_load_from_file,
        sample_yaml_config,
    ):
        """Test main function with keyboard interrupt."""
        mock_unified_config = Config(**sample_yaml_config)
        mock_load_from_file.return_value = mock_unified_config

        mock_daemon = Mock()
        mock_daemon.run.side_effect = KeyboardInterrupt()
        mock_components = {"daemon": mock_daemon}
        mock_create_components.return_value = mock_components

        with patch("sys.argv", ["main.py"]):
            result = main()

        assert result == 0


class TestCacheClearingFunctions:
    """Test cache clearing helper functions."""

    @patch("main.HikuDatabase")
    def test_clear_cache_for_keys_single_key(self, mock_hiku_db_class):
        """Test clear_cache_for_keys with single cache key."""
        from main import clear_cache_for_keys

        mock_db = Mock()
        mock_db.clear_cache_for_key.return_value = 5
        mock_hiku_db_class.return_value = mock_db

        result = clear_cache_for_keys("test.db", ["https://example.com"])

        mock_hiku_db_class.assert_called_once_with("test.db")
        mock_db.create_tables.assert_called_once()
        mock_db.clear_cache_for_key.assert_called_once_with("https://example.com")
        assert result == 5

    @patch("main.HikuDatabase")
    def test_clear_cache_for_keys_multiple_keys(self, mock_hiku_db_class):
        """Test clear_cache_for_keys with multiple cache keys."""
        from main import clear_cache_for_keys

        mock_db = Mock()
        mock_db.clear_cache_for_key.side_effect = [
            3,
            2,
            4,
        ]  # Deleted counts for each key
        mock_hiku_db_class.return_value = mock_db

        result = clear_cache_for_keys(
            "test.db",
            ["https://example1.com", "https://example2.com", "https://example3.com"],
        )

        mock_db.create_tables.assert_called_once()
        assert mock_db.clear_cache_for_key.call_count == 3
        assert result == 9  # 3 + 2 + 4

    @patch("main.HikuDatabase")
    def test_clear_cache_for_keys_returns_total_count(self, mock_hiku_db_class):
        """Test clear_cache_for_keys returns total deleted entries."""
        from main import clear_cache_for_keys

        mock_db = Mock()
        mock_db.clear_cache_for_key.side_effect = [2, 1]
        mock_hiku_db_class.return_value = mock_db

        result = clear_cache_for_keys("test.db", ["key1", "key2"])

        mock_db.create_tables.assert_called_once()
        assert result == 3  # Total from both keys

    @patch("main.HikuDatabase")
    def test_clear_all_cache_calls_database_method(self, mock_hiku_db_class):
        """Test clear_all_cache calls database method."""
        from main import clear_all_cache

        mock_db = Mock()
        mock_db.clear_all_cache.return_value = 10
        mock_hiku_db_class.return_value = mock_db

        result = clear_all_cache("test.db")

        mock_hiku_db_class.assert_called_once_with("test.db")
        mock_db.create_tables.assert_called_once()
        mock_db.clear_all_cache.assert_called_once()
        assert result == 10


class TestMainIntegration:
    """Test main function integration with cache clearing."""

    @patch("main.clear_all_cache")
    @patch("main.initialize_database")
    def test_main_clear_all_cache_returns_immediately(
        self, mock_init_db, mock_clear_all
    ):
        """Test main() calls clear_all_cache and returns 0."""
        mock_clear_all.return_value = 5

        test_args = ["--clear-all-cache", "--db-path", "test.db"]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        mock_clear_all.assert_called_once_with("test.db")

        assert result == 0

        mock_init_db.assert_not_called()

    @patch("main.clear_cache_for_keys")
    @patch("main.initialize_database")
    def test_main_clear_cache_keys_returns_immediately(
        self, mock_init_db, mock_clear_keys
    ):
        """Test main() calls clear_cache_for_keys and returns 0."""
        mock_clear_keys.return_value = 3

        test_args = [
            "--clear-cache-keys",
            "https://example.com",
            "https://example2.com",
            "--db-path",
            "test.db",
        ]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        mock_clear_keys.assert_called_once_with(
            "test.db", ["https://example.com", "https://example2.com"]
        )

        assert result == 0

        mock_init_db.assert_not_called()

    @patch("main.clear_all_cache")
    @patch("main.clear_cache_for_keys")
    @patch("main.initialize_database")
    def test_main_clear_all_cache_takes_precedence(
        self, mock_init_db, mock_clear_keys, mock_clear_all
    ):
        """Test main() prioritizes clear_all_cache over clear_cache_keys."""
        mock_clear_all.return_value = 10
        mock_clear_keys.return_value = 5

        test_args = [
            "--clear-all-cache",
            "--clear-cache-keys",
            "key1",
            "--db-path",
            "test.db",
        ]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        mock_clear_all.assert_called_once_with("test.db")

        mock_clear_keys.assert_not_called()

        assert result == 0

    @patch("main.clear_all_cache")
    @patch("yomu.config.config.Config.load_from_file")
    @patch("main.create_app_components")
    def test_main_clear_cache_ignores_other_operations(
        self, mock_create_components, mock_get_config, mock_clear_all
    ):
        """Test cache clearing doesn't trigger daemon startup."""
        mock_clear_all.return_value = 10

        mock_daemon = Mock()
        mock_components = {"daemon": mock_daemon}
        mock_create_components.return_value = mock_components

        test_args = ["--clear-all-cache", "--db-path", "test.db"]

        with patch("sys.argv", ["main.py"] + test_args):
            result = main()

        mock_get_config.assert_not_called()
        mock_create_components.assert_not_called()

        mock_daemon.run.assert_not_called()

        assert result == 0
