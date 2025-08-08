# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Yomu** is an email-driven newsletter aggregation tool that automatically collects, filters, and sends curated content from multiple sources via email. It uses LLM-powered extraction (via Hikugen) to intelligently parse web content, including both RSS feeds and arbitrary web pages.

Key characteristics:
- Single-user newsletter daemon with cron-based scheduling
- Content extraction delegates to Hikugen (external LLM service via OpenRouter)
- SQLite database for tracking source metadata and Hikugen cache
- SMTP integration for newsletter delivery (Gmail, Outlook, or any provider)
- YAML-based configuration for sources and frequencies
- Docker deployment ready

## Development Environment

### Prerequisites & Setup

- Python 3.11+ (see `.python-version`)
- `uv` package manager (installed via pip)
- SQLite (built-in)

### Common Development Commands

```bash
# Install dependencies
uv sync

# Run application with default settings
uv run main.py

# Initialize database (creates tables)
uv run main.py --init-db

# Clear all Hikugen cache
uv run main.py --clear-all-cache

# Clear cache for specific cache key(s)
uv run main.py --clear-cache-keys "https://example.com"

# Run with custom config and database
uv run main.py --config-file myconfig.yaml --db-path mydb.db

# Run with debug logging
uv run main.py --log-level DEBUG

# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run specific test function
uv run pytest tests/unit/test_config.py::test_load_config_success

# Run with coverage
uv run pytest --cov=src/yomu

# Format code with ruff
uv run ruff check --fix src/ tests/

# Lint with ruff
uv run ruff check src/ tests/

# Check with ruff without fixing
uv run ruff check src/ tests/
```

## Architecture

### High-Level Design

The application follows a layered architecture with clear separation of concerns:

1. **Configuration Layer** (`src/yomu/config/`): YAML-based config loading and validation
2. **Data Layer** (`src/yomu/database/`): SQLite operations for source metadata tracking
3. **Content Processing** (`src/yomu/content/`): Content extraction pipeline delegating to Hikugen
4. **Newsletter Generation** (`src/yomu/newsletter/`, `src/yomu/email/`): Newsletter building and email delivery
5. **Scheduling** (`src/yomu/daemon/`): Cron-based daemon loop for newsletter distribution
6. **Utilities** (`src/yomu/utils.py`): Shared logging, date parsing, and helper functions
7. **Entry Point** (`main.py`): CLI argument parsing and component initialization

### Key Modules

**Config** (`src/yomu/config/config.py`)
- Loads YAML configuration file
- Validates required fields: `openrouter_api_key`, `sender_email`, `sender_password`, `recipient_email`
- SMTP settings: `smtp_server` (default: smtp.gmail.com), `smtp_port` (default: 587)
- Optional fields: `cookie_file_path`, `max_articles_per_source`, `max_description_length`
- Validates `sources` (URLs) and `frequencies` (cron expressions)
- Validates SMTP port is in range 1-65535
- Singleton-like usage: `Config.load_from_file(path)`

**Database** (`src/yomu/database/database.py`)
- Lightweight SQLite wrapper with context manager support
- Tracks source metadata: URL + last_successful_run timestamp
- Used to filter articles by publication date (newer than last run)
- Does NOT manage Hikugen cache (that's separate via HikuDatabase)

**ContentProcessor** (`src/yomu/content/processor.py`)
- Main content extraction orchestrator
- Delegates HTML/RSS parsing to Hikugen (external LLM service)
- Filters articles by publication date against database
- Deduplicates articles using deque with circular buffer (max_fallback_urls)
- Parses multiple date formats (ISO, RFC2822, custom formats)
- Returns list of article dicts: `{title, url, description, published_date, source}`

**NewsletterService** (`src/yomu/newsletter/service.py`)
- Orchestrates end-to-end newsletter workflow
- Collects articles from all sources via ContentProcessor
- Generates HTML newsletter via HTMLTemplate
- Sends newsletter via EmailSender
- Handles failure logging

**NewsletterDaemon** (`src/yomu/daemon/daemon.py`)
- Infinite loop with cron-based scheduling
- Supports multiple cron schedules from config
- Calculates next run time across all schedules
- Dispatches newsletter generation at scheduled times

**EmailSender** (`src/yomu/email/sender.py`)
- SMTP integration (Gmail, Outlook, or any SMTP provider)
- Supports TLS (port 587) and SSL (port 465)
- Configurable sender email, password, SMTP server, and port
- Handles authentication and error recovery

**HTMLTemplate** (`src/yomu/email/templates.py`)
- Generates HTML newsletter structure
- Respects `max_articles_per_source` and `max_description_length` from config

### Data Flow

```
Config (YAML)
   ↓
Daemon Loop (Cron scheduling)
   ↓
NewsletterService.send_newsletter_to_user()
   ├→ ContentProcessor.process_source() [for each source]
   │  ├→ HikuExtractor (Hikugen/OpenRouter API)
   │  └→ Database (filter by last_successful_run)
   ├→ HTMLTemplate.generate_newsletter()
   └→ EmailSender.send_email()
   ↓
Database (update last_successful_run)
```

### Single-User Architecture

Yomu is explicitly designed for single-user deployment. There is:
- No user authentication system
- No multi-tenancy support
- One SQLite database per deployment
- One `recipient_email` per configuration

To run multiple newsletters, deploy multiple Yomu instances with separate configs.

## Testing Strategy

Tests are organized in `tests/` with two categories:

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
  - Config loading and validation
  - Date parsing utilities
  - Email template generation
  - Database CRUD operations
  - Content schema validation

- **Integration Tests** (`tests/integration/`): Test component interactions
  - Full newsletter generation workflow
  - Content processor + database integration
  - Email sender + service integration

All tests use real data and real APIs (not mocks). Test configuration files are in `tests/fixtures/`.

### Running Tests

```bash
# All tests
uv run pytest

# Specific category
uv run pytest tests/unit/
uv run pytest tests/integration/

# With verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

## Key Design Decisions

1. **Hikugen Delegation**: Content extraction is delegated to Hikugen (external service). Yomu focuses on orchestration, filtering, and delivery. This avoids reimplementing complex web scraping.

2. **Lightweight Database**: SQLite with minimal schema (`source_metadata` table) for tracking last-run timestamps. This is separate from Hikugen's own cache database.

3. **Multiple Cron Schedules**: The daemon supports multiple cron expressions, enabling complex scheduling (e.g., daily at 7:45 AM AND 5:00 PM).

4. **Date-Based Filtering**: Articles are filtered against `last_successful_run` from the database. Articles without publish dates fall back to a deque-based deduplication.

5. **Circular Buffer for Fallback**: For articles without publish dates, a deque with `maxlen` prevents unlimited memory growth while tracking recently processed URLs.

6. **Consolidated Utilities**: All shared functions (logging, date parsing, error handling) are in `utils.py` to avoid duplication.

## Configuration

Create `config.yaml` from `config.yaml.example`:

```yaml
openrouter_api_key: "your-key"
sender_email: "your-email@gmail.com"
sender_password: "your-app-password"

# SMTP Configuration (optional - defaults to Gmail)
smtp_server: "smtp.gmail.com"  # or your provider's SMTP server
smtp_port: 587                  # typically 587 for TLS, 465 for SSL

recipient_email: "recipient@example.com"

sources:
  - "https://example.com/rss"
  - "https://example.com"

frequencies:
  - "45 7 * * *"    # Daily at 7:45 AM
  - "0 17 * * *"    # Daily at 5:00 PM

max_articles_per_source: 10
max_description_length: 200
```

**SMTP Provider Examples:**
- Gmail: `smtp.gmail.com:587`
- Outlook: `smtp-mail.outlook.com:587`
- Custom servers: Configure `smtp_server` and `smtp_port` accordingly

## Deployment

### Docker

```bash
# Build image
docker build -t yomu .

# Run container (mounts config and data volumes)
docker run -v /path/to/config.yaml:/app/data/config.yaml \
           -v /path/to/data:/app/data \
           yomu
```

The Dockerfile:
- Uses Python 3.11 slim base image
- Installs `uv` for dependency management
- Runs `uv sync --frozen` to lock dependencies
- Creates non-root `yomu` user for security
- Initializes database and starts daemon on container startup

### Local Execution

```bash
uv sync
uv run main.py --config-file config.yaml --db-path yomu.db
```

## Recent Refactoring Context

Recent commits focused on code quality and simplification:
- Consolidated utility modules into single `utils.py`
- Removed redundant error handling anti-patterns
- Eliminated duplicate article processing logic
- Removed unused wrapper methods and parameters
- Renamed project from "Ima" to "Yomu"
- Consolidated date parsing (single location for all date format handling)
- Made SMTP configuration provider-agnostic (no longer Gmail-only):
  - `gmail_email` → `sender_email`
  - `gmail_app_password` → `sender_password`
  - `user_email` → `recipient_email`
  - Added configurable `smtp_server` and `smtp_port`

See git log for details: `git log --oneline`.

## Common Issues & Troubleshooting

**Database Lock Issues**
- Yomu uses `check_same_thread=False` for SQLite connections to support the daemon loop
- Ensure only one daemon instance accesses the database at a time

**Hikugen Cache Grows Large**
- Clear cache with: `uv run main.py --clear-all-cache`
- Or for specific sources: `uv run main.py --clear-cache-keys "https://example.com"`

**Articles Not Appearing**
- Check `max_articles_per_source` setting in config (default: 3)
- Check `last_successful_run` timestamp in database
- Enable debug logging: `uv run main.py --log-level DEBUG`

**Email Not Sending**
- Verify sender password is correct for your SMTP provider
- For Gmail: Use app password (not regular password), ensure App Passwords are enabled
- For Outlook: Use app password or app-specific password
- Verify `smtp_server` and `smtp_port` match your provider
- Verify `recipient_email` is valid in config
- Enable debug logging to see SMTP connection errors: `uv run main.py --log-level DEBUG`
