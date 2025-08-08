# ABOUTME: Test suite for database schema and operations
# ABOUTME: Tests SQLite database functionality for sources in single-user architecture

import pytest
import sqlite3
from yomu.database.database import Database


@pytest.fixture
def temp_db():
    """Create an in-memory database for testing."""
    db = Database(":memory:")
    yield db
    db.close()


class TestDatabaseSchema:
    """Test database table creation and schema."""

    def test_create_tables(self, temp_db):
        """Test that only source_metadata table is created with correct schema."""
        temp_db.create_tables()

        cursor = temp_db.connection.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "source_metadata" in tables
        assert "users" not in tables
        assert "subscriptions" not in tables
        assert len(tables) == 1

        cursor.execute("PRAGMA table_info(source_metadata)")
        sources_columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "url" in sources_columns
        assert "last_successful_run" in sources_columns
        assert sources_columns["url"] == "TEXT"
        assert "extraction_code" not in sources_columns


class TestSourceOperations:
    """Test source CRUD operations."""

    def test_get_source_by_url(self, temp_db):
        """Test getting a single source by URL."""
        temp_db.create_tables()

        url1 = "https://example.com/feed1"
        url2 = "https://example.com/feed2"

        temp_db.add_source(url1)
        temp_db.add_source(url2)

        source = temp_db.get_source_by_url(url1)
        assert source is not None
        assert source["url"] == url1

        source = temp_db.get_source_by_url("https://nonexistent.com")
        assert source is None


class TestDatabaseContextManager:
    """Test database connection management."""

    def test_close_connection(self, temp_db):
        """Test that database connection can be closed."""
        temp_db.create_tables()
        temp_db.close()

        with pytest.raises(sqlite3.ProgrammingError):
            temp_db.connection.execute("SELECT 1")
