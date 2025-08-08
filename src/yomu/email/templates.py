# ABOUTME: HTML email template generation for modern minimalist newsletters
# ABOUTME: Provides clean, responsive email templates with professional typography

import html
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from yomu.utils import truncate_description, format_readable_date

if TYPE_CHECKING:
    from yomu.config.config import Config


class HTMLTemplate:
    """Modern minimalist HTML email template generator."""

    def __init__(self, config: Optional["Config"] = None):
        """Initialize HTMLTemplate with base styles and optional configuration.

        Args:
            config: Optional configuration object for template customization
        """
        self.config = config
        self.base_styles = self._get_base_styles()

    def generate_newsletter(
        self, articles_by_source: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Generate complete HTML newsletter from articles.

        Args:
            articles_by_source: Dictionary mapping source names to article lists

        Returns:
            Complete HTML email content
        """
        if not articles_by_source:
            return self._generate_empty_newsletter()

        # Generate newsletter sections
        header = self._generate_header()
        content = self._generate_content(articles_by_source)
        footer = self._generate_footer()

        # Combine into complete HTML document
        return self._wrap_in_html_document(header + content + footer)

    def _get_base_styles(self) -> str:
        """Get base CSS styles for the email template.

        Returns:
            CSS styles as string
        """
        return """
        <style>
            /* Reset and base styles */
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
                line-height: 1.35;
                margin: 0;
                padding: 0;
            }

            .newsletter-container {
                max-width: 600px;
                margin: 0 auto;
                padding: 16px 12px;
            }

            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 1px solid;
            }

            .header h1 {
                font-size: 22px;
                font-weight: 500;
                margin: 0;
                letter-spacing: -0.02em;
            }

            .header p {
                font-size: 12px;
                margin: 0;
                font-weight: 400;
                white-space: nowrap;
            }

            .source-section {
                margin-bottom: 16px;
            }

            .source-header {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
                padding-bottom: 2px;
                border-bottom: 1px solid;
                letter-spacing: -0.01em;
            }

            .source-header a {
                text-decoration: none;
                transition: opacity 0.2s ease;
            }

            .source-header a:hover {
                text-decoration: none;
            }

            .article {
                margin-bottom: 10px;
                padding-bottom: 8px;
            }

            .article:last-child {
                margin-bottom: 0;
                padding-bottom: 0;
            }

            .article-title {
                font-size: 15px;
                font-weight: 600;
                margin-bottom: 6px;
                line-height: 1.3;
                letter-spacing: -0.01em;
            }

            .article-title a {
                text-decoration: none;
                transition: opacity 0.2s ease;
            }

            .article-title a:hover {
                text-decoration: underline;
            }

            .article-date {
                font-size: 11px;
                margin-bottom: 4px;
            }

            .article-description {
                font-size: 13px;
                margin-bottom: 6px;
                line-height: 1.4;
            }

            .article-meta {
                font-size: 12px;
                display: none;
            }

            .article-link {
                text-decoration: none;
                font-weight: 500;
                transition: opacity 0.2s ease;
            }

            .article-link:hover {
                text-decoration: underline;
            }

            .footer {
                margin-top: 16px;
                padding-top: 8px;
                border-top: 1px solid;
                text-align: center;
                font-size: 11px;
            }

            .footer p {
                margin-bottom: 2px;
            }

            .footer a {
                text-decoration: none;
            }

            .footer a:hover {
                text-decoration: underline;
            }

            /* Mobile responsiveness */
            @media only screen and (max-width: 600px) {
                .newsletter-container {
                    padding: 12px 10px;
                }

                .header {
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 4px;
                }

                .header h1 {
                    font-size: 20px;
                }

                .header p {
                    font-size: 11px;
                }

                .source-header {
                    font-size: 15px;
                }

                .article-date {
                    font-size: 10px;
                }
            }
        </style>
        """

    def _generate_header(self) -> str:
        """Generate newsletter header.

        Returns:
            HTML header content
        """
        return """<div class="header">
            <h1>Your Newsletter</h1>
        </div>"""

    def _generate_content(
        self, articles_by_source: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Generate main newsletter content from articles.

        Args:
            articles_by_source: Dictionary mapping source names to article lists

        Returns:
            HTML content for articles
        """
        content_parts = []

        # Preserve source order from config (dict maintains insertion order)
        for source_name in articles_by_source.keys():
            source_data = articles_by_source[source_name]

            # Handle both new structure {"url": url, "articles": articles} and old structure [articles]
            if isinstance(source_data, dict) and "articles" in source_data:
                # New structure with URL
                articles = source_data["articles"]
                source_url = source_data.get("url")
            else:
                # Old structure (backward compatibility)
                articles = source_data
                source_url = None

            if not articles:
                continue

            content_parts.append(
                self._generate_source_section(source_name, articles, source_url)
            )

        return "\n".join(content_parts)

    def _generate_source_section(
        self, source_name: str, articles: List[Dict[str, Any]], source_url: str = None
    ) -> str:
        """Generate HTML for a single source section.

        Args:
            source_name: Name of the source
            articles: List of articles from this source
            source_url: URL of the source (optional, for clickable headers)

        Returns:
            HTML content for source section
        """
        # Escape source name for HTML
        escaped_source_name = html.escape(source_name)

        # Generate source header with optional link
        if source_url:
            source_header = f'<a href="{html.escape(source_url)}" target="_blank">{escaped_source_name}</a>'
        else:
            source_header = escaped_source_name

        # Generate articles HTML
        articles_html = []
        for article in articles:
            articles_html.append(self._generate_article(article))

        return f"""<div class="source-section">
            <h2 class="source-header">{source_header}</h2>
            {"".join(articles_html)}
        </div>"""

    def _generate_article(self, article: Dict[str, Any]) -> str:
        """Generate HTML for a single article.

        Args:
            article: Article data dictionary

        Returns:
            HTML content for article
        """
        # Extract and escape article data, handling None values
        title = html.escape(str(article.get("title") or "No Title"))
        link = html.escape(str(article.get("link") or ""))
        description = str(article.get("description") or "")
        pub_date = article.get("pubDate") or ""

        # Apply description truncation if config is available
        if self.config and description:
            description = truncate_description(
                description, self.config.max_description_length
            )

        # Format publication date
        if not pub_date:
            formatted_date = ""
        else:
            formatted_date = format_readable_date(pub_date) or ""

        # Generate title with optional link
        if link:
            title_html = f'<a href="{link}" target="_blank">{title}</a>'
        else:
            title_html = title

        # Generate date div if available
        date_html = (
            f'<div class="article-date">{formatted_date}</div>'
            if formatted_date
            else ""
        )

        # Generate description if available
        description_html = (
            f'<div class="article-description">{description}</div>'
            if description
            else ""
        )

        return f"""<div class="article">
            {date_html}
            <h3 class="article-title">{title_html}</h3>
            {description_html}
        </div>"""

    def _generate_footer(self) -> str:
        """Generate newsletter footer.

        Returns:
            HTML footer content
        """
        return """<div class="footer">
            <p>You're receiving this newsletter because you subscribed via email.</p>
            <p>Generated by <a href="#">Yomu Newsletter</a></p>
        </div>"""

    def _generate_empty_newsletter(self) -> str:
        """Generate HTML for empty newsletter.

        Returns:
            HTML content for empty newsletter
        """
        header = self._generate_header()
        content = """
        <div style="text-align: center; padding: 40px 20px; color: #666666;">
            <p>No new articles this time. Check back later!</p>
        </div>
        """
        footer = self._generate_footer()

        return self._wrap_in_html_document(header + content + footer)

    def _wrap_in_html_document(self, content: str) -> str:
        """Wrap content in complete HTML document.

        Args:
            content: HTML content to wrap

        Returns:
            Complete HTML document
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>Your Newsletter</title>
    {self.base_styles}
</head>
<body>
    <div class="newsletter-container">
        {content}
    </div>
</body>
</html>"""
