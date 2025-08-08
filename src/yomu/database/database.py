# ABOUTME: SQLite database operations for Yomu newsletter app
# ABOUTME: Implements CRUD operations for source_metadata table with SQLite

import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

SOURCE_METADATA_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS source_metadata (
        url TEXT PRIMARY KEY,
        last_successful_run TEXT
    )
"""


class Database:
    """SQLite database manager for Yomu newsletter application."""

    def __init__(self, db_path: str = "yomu.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        # Enable foreign key constraints
        self.connection.execute("PRAGMA foreign_keys = ON")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()

    def create_tables(self):
        """Create source_metadata table for single-user architecture."""
        cursor = self.connection.cursor()

        cursor.execute(SOURCE_METADATA_TABLE_SQL)

        self.connection.commit()

    def add_source(self, url: str):
        """Add a source to the database.

        Args:
            url: Source URL (primary key)
        """
        cursor = self.connection.cursor()

        try:
            cursor.execute(
                "INSERT INTO source_metadata (url, last_successful_run) VALUES (?, NULL)",
                (url,),
            )
        except sqlite3.IntegrityError:
            # Source already exists, nothing to update
            pass

        self.connection.commit()

    def update_source_last_run(self, url: str, timestamp: datetime):
        """Update source's last successful run timestamp.

        Args:
            url: Source URL
            timestamp: Last successful extraction timestamp
        """
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE source_metadata SET last_successful_run = ? WHERE url = ?",
            (timestamp.isoformat(), url),
        )
        self.connection.commit()

    def get_source_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Get a source by its URL.

        Args:
            url: Source URL to look up

        Returns:
            Source dictionary or None if not found
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM source_metadata WHERE url = ?", (url,))
        row = cursor.fetchone()
        return dict(row) if row else None
