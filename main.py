# ABOUTME: Main application entry point for Yomu newsletter daemon
# ABOUTME: Provides CLI interface, component initialization

import sys
import argparse
import logging
from typing import Dict, Any, List

from yomu.config.config import Config
from yomu.database.database import Database
from yomu.email.sender import EmailSender
from yomu.content.processor import ContentProcessor
from yomu.newsletter.service import NewsletterService
from yomu.daemon.daemon import NewsletterDaemon
from yomu.utils import setup_logger, get_logger
from hikugen.database import HikuDatabase

logger = get_logger(__name__)


def parse_arguments(args=None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: List of arguments to parse (for testing)

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Yomu - Email-driven Newsletter Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                   # Run with default settings
  python main.py --config-file my-config.yaml      # Use custom YAML config file
  python main.py --init-db                         # Initialize database tables
  python main.py --db-path /data/yomu.db           # Use custom database path
  python main.py --log-level DEBUG                 # Enable debug logging

  Use config.yaml.example as template
        """,
    )

    parser.add_argument(
        "--config-file",
        type=str,
        default="config.yaml",
        help="Path to YAML configuration file (default: config.yaml)",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="yomu.db",
        help="Path to SQLite database file (default: yomu.db)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--init-db", action="store_true", help="Initialize database tables"
    )

    parser.add_argument(
        "--clear-all-cache",
        action="store_true",
        help="Clear all cached extraction code",
    )

    parser.add_argument(
        "--clear-cache-keys",
        nargs="*",
        default=None,
        help="Clear cached extraction code for specific cache keys",
    )

    parser.add_argument("--version", action="version", version="0.1.0")

    return parser.parse_args(args)


def initialize_database(db_path: str):
    """Initialize database with required tables.

    Args:
        db_path: Path to SQLite database file
    """
    logger.info(f"Initializing database at {db_path}")
    with Database(db_path) as db:
        db.create_tables()
        logger.info("Database tables created successfully")


def clear_cache_for_keys(db_path: str, cache_keys: List[str]) -> int:
    """Clear Hikugen cache for specific cache keys.

    Args:
        db_path: Path to SQLite database file
        cache_keys: List of cache keys (URLs or task names) to clear

    Returns:
        Total number of cache entries deleted
    """
    logger.info(f"Clearing Hikugen cache for {len(cache_keys)} cache key(s)")
    hiku_db = HikuDatabase(db_path)
    hiku_db.create_tables()
    total_deleted = 0

    for cache_key in cache_keys:
        count = hiku_db.clear_cache_for_key(cache_key)
        total_deleted += count
        logger.debug(f"Cleared {count} entries for cache key: {cache_key}")

    logger.info(
        f"Cleared Hikugen cache for {len(cache_keys)} key(s), deleted {total_deleted} entries total"
    )
    return total_deleted


def clear_all_cache(db_path: str) -> int:
    """Clear all Hikugen cached extraction code.

    Args:
        db_path: Path to SQLite database file

    Returns:
        Total number of cache entries deleted
    """
    hiku_db = HikuDatabase(db_path)
    hiku_db.create_tables()
    count = hiku_db.clear_all_cache()

    logger.info(f"Cleared all Hikugen cache, deleted {count} entries")
    return count


def create_app_components(config: Config, db_path: str) -> Dict[str, Any]:
    """Create and wire together all application components.

    Args:
        config: Unified configuration (API keys, SMTP, user email, sources, frequency)
        db_path: Path to database file

    Returns:
        Dictionary of initialized components
    """
    database = Database(db_path)

    email_sender = EmailSender(config)

    content_processor = ContentProcessor(config, database, db_path)

    newsletter_service = NewsletterService(config, content_processor, email_sender)

    daemon = NewsletterDaemon(config, newsletter_service)

    return {
        "database": database,
        "email_sender": email_sender,
        "content_processor": content_processor,
        "newsletter_service": newsletter_service,
        "daemon": daemon,
    }


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        args = parse_arguments()

        setup_logger(level=getattr(logging, args.log_level))

        logger.info("Starting Yomu Newsletter Application")
        logger.info(f"Database path: {args.db_path}")
        logger.info(f"Log level: {args.log_level}")

        if args.clear_all_cache:
            clear_all_cache(args.db_path)
            return 0

        if args.clear_cache_keys is not None and args.clear_cache_keys:
            clear_cache_for_keys(args.db_path, args.clear_cache_keys)
            return 0

        if args.init_db:
            initialize_database(args.db_path)
            return 0

        config = Config.load_from_file(args.config_file)

        components = create_app_components(config, args.db_path)

        logger.info("Starting newsletter daemon...")
        components["daemon"].run()
        logger.info("Application shutdown complete")
        return 0

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0

    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
