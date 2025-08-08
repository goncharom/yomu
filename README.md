# Yomu - AI-powered email newsletter aggregator

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Email-driven newsletter daemon that automatically collects and sends content from multiple sources using AI-powered extraction.

## Overview

Yomu monitors RSS feeds and web pages, extracts relevant content using LLMs (via [Hikugen](https://github.com/goncharom/hikugen)), and delivers curated newsletters on a schedule you define. Given a list of content sources and cron-based frequencies, Yomu:

1. Fetches content from your sources (RSS feeds or web pages)
2. Extracts articles using Hikugen's LLM-powered extraction
3. Filters articles by publication date
4. Generates an HTML newsletter
5. Sends via SMTP on schedule

![sc.png](.github/sc.png)

## Quick Start

### Prerequisites

- Python 3.11+
- OpenRouter API key
- SMTP credentials (Gmail, Outlook, or any SMTP provider)

### Installation

```bash
git clone https://github.com/goncharom/yomu.git
cd yomu
uv sync
```

### Configuration

Copy the example config and customize:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your settings:

```yaml
# API Configuration
openrouter_api_key: "your-openrouter-api-key-here"
sender_email: "your-email@gmail.com"
sender_password: "your-app-password"

# SMTP Configuration (optional - defaults to Gmail)
smtp_server: "smtp.gmail.com"  # or your provider's SMTP server
smtp_port: 587                  # typically 587 for TLS, 465 for SSL

# Newsletter Configuration
recipient_email: "recipient@example.com"  # Where newsletters will be sent

# You can use the same email as both sender and recipient

sources:
  - "https://feeds.feedburner.com/oreilly/radar"
  - "https://rss.cnn.com/rss/edition.rss"
  - "https://news.ycombinator.com"

frequencies:
  - "45 7 * * *"    # Daily at 7:45 AM
  - "0 17 * * *"    # Daily at 5:00 PM

max_articles_per_source: 10
max_description_length: 200
```

**For Gmail users:** Follow [this guide](https://support.google.com/mail/answer/185833?hl=en) to create an App Password for if you plan to use Gmail.

**For other SMTP providers:** Update `smtp_server` and `smtp_port` accordingly (e.g., `smtp.outlook.com:587` for Outlook).

### Running

```bash
# Initialize database
uv run main.py --init-db

# Start daemon
uv run main.py --config-file config.yaml

# Or with custom database path
uv run main.py --config-file config.yaml --db-path /data/yomu.db

# Enable debug logging
uv run main.py --log-level DEBUG
```

## Docker setup

```bash
# Place your config in ./data/config.yaml
cp data/config.yaml.example data/config.yaml
# Edit data/config.yaml with your settings

# Build and run with docker-compose
docker-compose up
```

The container will initialize the database and start the daemon automatically.

## Cache Management

Clear Hikugen's cached extraction code when page structures change:

```bash
# Clear cache for specific sources
uv run main.py --clear-cache-keys "https://example.com" "https://another.com"

# Clear all cached extraction code
uv run main.py --clear-all-cache
```

## See Also

- [CLAUDE.md](./CLAUDE.md) - Development guide and architecture
- [Hikugen](https://github.com/goncharom/hikugen) - AI-powered web scraping library

## License

See LICENSE file for details.
