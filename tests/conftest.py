# ABOUTME: Pytest configuration and fixtures for Yomu tests
# ABOUTME: Provides shared test fixtures and configuration for all tests

import pytest
import os
from unittest.mock import patch


def pytest_configure(config):
    """Register pytest markers for test categorization."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")

@pytest.fixture
def mock_env_vars():
    """Fixture providing mock environment variables for testing."""
    return {
        "OPENROUTER_API_KEY": "test-api-key",
        "SENDER_EMAIL": "test@gmail.com",
        "SENDER_PASSWORD": "test-app-password",
    }


@pytest.fixture
def config_env(mock_env_vars):
    """Fixture that patches environment variables for config testing."""
    with patch.dict(os.environ, mock_env_vars, clear=True):
        yield mock_env_vars
