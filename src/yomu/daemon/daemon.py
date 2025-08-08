# ABOUTME: Main daemon loop for Yomu newsletter scheduling and distribution
# ABOUTME: Orchestrates newsletter distribution based on cron-scheduled timing from YAML configuration

import time
from datetime import datetime
from croniter import croniter
from yomu.config.config import Config
from yomu.newsletter.service import NewsletterService
from yomu.utils import get_logger


class NewsletterDaemon:
    """Main daemon for newsletter distribution with cron-based scheduling."""

    def __init__(self, config: Config, newsletter_service: NewsletterService):
        """Initialize NewsletterDaemon with multiple cron-based scheduling.

        Args:
            config: Unified configuration with recipient email, sources, and frequencies
            newsletter_service: NewsletterService for generating and sending newsletters

        Raises:
            ValueError: If any frequency cron expression cannot be parsed
        """
        self.config = config
        self.newsletter_service = newsletter_service
        self.logger = get_logger(__name__)

        # Initialize cron iterators for multiple schedules - fail fast if invalid
        self.crons = []
        for frequency in self.config.frequencies:
            cron = croniter(frequency, datetime.now())
            self.crons.append(cron)

    def run(self):
        """Run the main daemon loop with cron-based scheduling."""
        while True:
            next_run_time = self._get_next_run_time()
            current_time = datetime.now()
            self.logger.info(f"Next newsletter scheduled for: {next_run_time}")
            time.sleep((next_run_time - current_time).total_seconds())
            self.newsletter_service.send_newsletter_to_user(
                self.config.recipient_email, self.config.sources
            )

    def _get_next_run_time(self) -> datetime:
        """Get the earliest next run time across all cron schedules."""
        current_time = datetime.now()
        next_times = []
        for cron in self.crons:
            cron.set_current(current_time)
            next_times.append(cron.get_next(datetime))

        return min(next_times)
