# ABOUTME: Test suite for HTML email template generation
# ABOUTME: Tests HTMLTemplate class for modern email formatting and structure

import pytest
from yomu.email.templates import HTMLTemplate


class TestHTMLTemplate:
    """Test HTMLTemplate class functionality."""

    @pytest.fixture
    def template(self):
        """Create HTMLTemplate instance."""
        return HTMLTemplate()

    @pytest.fixture
    def sample_articles(self):
        """Sample article data for testing."""
        return {
            "Tech Blog": [
                {
                    "title": "Latest Tech News",
                    "link": "https://example.com/tech-news",
                    "description": "This is a sample tech article description.",
                    "pubDate": "Mon, 01 Jan 2023 10:00:00 GMT",
                },
                {
                    "title": "Another Tech Article",
                    "link": "https://example.com/another-tech",
                    "description": "Another sample article about technology.",
                    "pubDate": "Tue, 02 Jan 2023 15:30:00 GMT",
                },
            ],
            "News Site": [
                {
                    "title": "Breaking News",
                    "link": "https://news.com/breaking",
                    "description": "Important news update.",
                    "pubDate": "Wed, 03 Jan 2023 09:15:00 GMT",
                }
            ],
        }

    def test_generate_newsletter_with_articles(self, template, sample_articles):
        """Test generating HTML newsletter with articles."""
        newsletter = template.generate_newsletter(sample_articles)

        assert newsletter.startswith("<!DOCTYPE html>")
        assert '<html lang="en">' in newsletter
        assert "<head>" in newsletter
        assert "<body>" in newsletter
        assert "</body>" in newsletter
        assert "</html>" in newsletter

        assert "<style>" in newsletter
        assert "font-family:" in newsletter
        assert ".newsletter-container" in newsletter
        assert ".article" in newsletter

        assert "newsletter-container" in newsletter

        assert "Your Newsletter" in newsletter

        assert "Tech Blog" in newsletter
        assert "News Site" in newsletter

        assert "Latest Tech News" in newsletter
        assert "Another Tech Article" in newsletter
        assert "Breaking News" in newsletter

        assert "https://example.com/tech-news" in newsletter
        assert "https://example.com/another-tech" in newsletter
        assert "https://news.com/breaking" in newsletter

        assert "This is a sample tech article description." in newsletter
        assert "Another sample article about technology." in newsletter
        assert "Important news update." in newsletter

        assert "You're receiving this newsletter" in newsletter
        assert "Yomu Newsletter" in newsletter

    def test_generate_empty_newsletter(self, template):
        """Test generating newsletter with no articles."""
        newsletter = template.generate_newsletter({})

        assert newsletter.startswith("<!DOCTYPE html>")
        assert '<html lang="en">' in newsletter
        assert "<body>" in newsletter
        assert "</body>" in newsletter
        assert "</html>" in newsletter

        assert "No new articles this time" in newsletter
        assert "Check back later!" in newsletter

        assert "Your Newsletter" in newsletter
        assert "You're receiving this newsletter" in newsletter

    def test_html_escaping(self, template):
        """Test that HTML content is properly escaped."""
        articles_with_html = {
            "Test Source": [
                {
                    "title": 'Article with <script>alert("xss")</script> in title',
                    "link": "https://example.com/safe",
                    "description": "Description with <b>bold</b> and & symbols",
                    "pubDate": "Mon, 01 Jan 2023 10:00:00 GMT",
                }
            ]
        }

        newsletter = template.generate_newsletter(articles_with_html)

        assert "&lt;script&gt;" in newsletter

        assert "<b>bold</b>" in newsletter
        assert (
            "and & symbols" in newsletter
        )  # & symbols are not escaped in descriptions

        assert "<script>" not in newsletter
        assert 'alert("xss")' not in newsletter

    def test_article_without_optional_fields(self, template):
        """Test handling articles with missing optional fields."""
        minimal_articles = {"Simple Source": [{"title": "Minimal Article"}]}

        newsletter = template.generate_newsletter(minimal_articles)

        assert newsletter.startswith("<!DOCTYPE html>")
        assert "Minimal Article" in newsletter
        assert "Simple Source" in newsletter

        assert "No Title" not in newsletter  # Should use provided title

    def test_multiple_sources_config_order(self, template):
        """Test that sources are ordered according to config file order."""
        config_order_articles = {
            "Zebra News": [{"title": "Last Article"}],
            "Alpha Blog": [{"title": "First Article"}],
            "Beta Site": [{"title": "Middle Article"}],
        }

        newsletter = template.generate_newsletter(config_order_articles)

        zebra_pos = newsletter.find("Zebra News")
        alpha_pos = newsletter.find("Alpha Blog")
        beta_pos = newsletter.find("Beta Site")

        assert zebra_pos != -1 and alpha_pos != -1 and beta_pos != -1
        assert zebra_pos < alpha_pos < beta_pos

    def test_responsive_css_included(self, template):
        """Test that responsive CSS is included."""
        newsletter = template.generate_newsletter({})

        assert "@media only screen and (max-width: 600px)" in newsletter
        assert "max-width: 600px" in newsletter

        assert "box-sizing: border-box" in newsletter
        assert "transition:" in newsletter

    def test_accessibility_features(self, template):
        """Test that accessibility features are included."""
        newsletter = template.generate_newsletter({})

        assert 'lang="en"' in newsletter
        assert "<h1>" in newsletter

        assert newsletter.count("<h1>") == 1  # Only one main heading

    def test_compact_design_spacing(self, template):
        """Test that the design uses compact spacing values."""
        newsletter = template.generate_newsletter({})

        assert "padding: 16px 12px" in newsletter

        assert "margin-bottom: 12px" in newsletter  # header
        assert "margin-bottom: 16px" in newsletter  # source section
        assert "margin-bottom: 8px" in newsletter  # source header
        assert "margin-top: 16px" in newsletter  # footer

        assert "padding-bottom: 8px" in newsletter

        assert "gap: 4px" in newsletter

    def test_modern_typography(self, template):
        """Test that modern typography features are applied."""
        newsletter = template.generate_newsletter({})

        assert "letter-spacing: -0.02em" in newsletter  # main title
        assert "letter-spacing: -0.01em" in newsletter  # section headers

        assert "font-size: 22px" in newsletter  # main title
        assert "font-size: 16px" in newsletter  # source headers
        assert "font-size: 15px" in newsletter  # article titles
        assert "font-size: 13px" in newsletter  # descriptions
        assert "font-size: 12px" in newsletter  # meta text

        assert "font-family:" in newsletter
        assert "-apple-system" in newsletter or "BlinkMacSystemFont" in newsletter

    def test_mobile_compact_responsiveness(self, template):
        """Test that mobile styles are also compact."""
        newsletter = template.generate_newsletter({})

        mobile_css = newsletter[newsletter.find("@media") : newsletter.find("</style>")]
        assert "padding: 12px 10px" in mobile_css
        assert "gap: 4px" in mobile_css  # mobile title gap

    def test_generate_newsletter_with_source_urls(self, template):
        """Test generating newsletter with new structure containing source URLs."""
        articles_with_urls = {
            "Hacker News": {
                "url": "https://news.ycombinator.com",
                "articles": [
                    {
                        "title": "Show HN: My Project",
                        "link": "https://example.com/project",
                        "description": "A cool project",
                        "pubDate": "Mon, 01 Jan 2023 10:00:00 GMT",
                    }
                ],
            },
            "TechCrunch": {
                "url": "https://techcrunch.com",
                "articles": [
                    {
                        "title": "Tech News",
                        "link": "https://techcrunch.com/news",
                        "description": "Latest tech news",
                        "pubDate": "Tue, 02 Jan 2023 12:00:00 GMT",
                    }
                ],
            },
        }

        newsletter = template.generate_newsletter(articles_with_urls)

        assert newsletter.startswith("<!DOCTYPE html>")
        assert "Your Newsletter" in newsletter

        assert (
            '<a href="https://news.ycombinator.com" target="_blank">Hacker News</a>'
            in newsletter
        )
        assert (
            '<a href="https://techcrunch.com" target="_blank">TechCrunch</a>'
            in newsletter
        )

        assert "Show HN: My Project" in newsletter
        assert "Tech News" in newsletter
        assert "https://example.com/project" in newsletter
        assert "https://techcrunch.com/news" in newsletter

    def test_source_header_links_have_proper_styling(self, template):
        """Test that source header links have proper CSS styling."""
        articles_with_urls = {
            "Example Source": {
                "url": "https://example.com",
                "articles": [
                    {
                        "title": "Test Article",
                        "link": "https://example.com/article",
                        "description": "Test description",
                    }
                ],
            }
        }

        newsletter = template.generate_newsletter(articles_with_urls)

        assert ".source-header a" in newsletter
        assert "text-decoration: none" in newsletter  # No underline by default

        assert ".source-header a:hover" in newsletter

    def test_fallback_for_old_structure_without_urls(self, template):
        """Test that template still works with old structure (no URLs)."""
        old_structure_articles = {
            "Legacy Source": [
                {
                    "title": "Legacy Article",
                    "link": "https://example.com/legacy",
                    "description": "Legacy description",
                }
            ]
        }

        newsletter = template.generate_newsletter(old_structure_articles)

        assert newsletter.startswith("<!DOCTYPE html>")
        assert "Legacy Source" in newsletter
        assert "Legacy Article" in newsletter

        assert (
            "<a href=" not in newsletter
            or "Legacy Source"
            not in newsletter[newsletter.find("<a href=") : newsletter.find("</a>") + 5]
        )

    def test_mixed_structure_handling(self, template):
        """Test that template handles mixed old and new structures gracefully."""
        mixed_articles = {
            "New Source": {
                "url": "https://newsource.com",
                "articles": [{"title": "New Article"}],
            },
            "Old Source": [{"title": "Old Article"}],
        }

        newsletter = template.generate_newsletter(mixed_articles)

        assert "New Source" in newsletter
        assert "Old Source" in newsletter
        assert "New Article" in newsletter
        assert "Old Article" in newsletter

    def test_source_links_open_in_new_tab(self, template):
        """Test that source header links open in new tab."""
        articles_with_urls = {
            "External Source": {
                "url": "https://external.com",
                "articles": [{"title": "External Article"}],
            }
        }

        newsletter = template.generate_newsletter(articles_with_urls)

        assert 'target="_blank"' in newsletter
        assert '<a href="https://external.com" target="_blank"' in newsletter

    def test_flat_article_layout_no_cards(self, template, sample_articles):
        """Test that articles use flat layout without card styling."""
        newsletter = template.generate_newsletter(sample_articles)

        assert "background-color: #f8f9fa" not in newsletter

        assert "border-radius: 6px" not in newsletter

        assert "border-left: 3px solid #007aff" not in newsletter

        article_css_start = newsletter.find(".article {")
        article_css_end = newsletter.find("}", article_css_start)
        article_css = newsletter[article_css_start : article_css_end + 1]

        assert "background-color:" not in article_css
        assert "border-left:" not in article_css
        assert "border-radius:" not in article_css
        assert "border-bottom:" not in article_css  # No dividers, clean layout
        assert "margin-bottom:" in article_css
        assert "padding-bottom:" in article_css

        assert "article-title" in newsletter
        assert "article-description" in newsletter
        assert "article-meta" in newsletter

    def test_flat_layout_maintains_readability(self, template, sample_articles):
        """Test that flat layout maintains proper spacing and readability."""
        newsletter = template.generate_newsletter(sample_articles)

        assert "margin-bottom:" in newsletter

        assert "font-size: 15px" in newsletter  # article titles
        assert "font-size: 13px" in newsletter  # descriptions
        assert "font-weight: 600" in newsletter  # title weight

        assert 'class="article"' in newsletter

    def test_description_truncation_at_limit(self, template):
        """Test that descriptions are truncated at the exact character limit."""
        from yomu.config.config import Config

        config = Config(
            openrouter_api_key="test",
            sender_email="test@gmail.com",
            sender_password="test",
            recipient_email="user@test.com",
            sources=["https://test.com"],
            frequencies=["0 9 * * *"],
            max_description_length=50,
        )

        template_with_config = HTMLTemplate(config)

        long_description = "This is a very long description that definitely exceeds fifty characters and should be truncated properly"
        articles = {
            "Test Source": [
                {
                    "title": "Test Article",
                    "link": "https://example.com/test",
                    "description": long_description,
                    "pubDate": "Mon, 01 Jan 2023 10:00:00 GMT",
                }
            ]
        }

        newsletter = template_with_config.generate_newsletter(articles)

        assert "This is a very long description that..." in newsletter
        assert long_description not in newsletter

    def test_description_no_truncation_under_limit(self, template):
        """Test that descriptions shorter than limit are not truncated."""
        from yomu.config.config import Config

        config = Config(
            openrouter_api_key="test",
            sender_email="test@gmail.com",
            sender_password="test",
            recipient_email="user@test.com",
            sources=["https://test.com"],
            frequencies=["0 9 * * *"],
            max_description_length=200,
        )

        template_with_config = HTMLTemplate(config)

        short_description = "This is a short description."
        articles = {
            "Test Source": [
                {
                    "title": "Test Article",
                    "description": short_description,
                }
            ]
        }

        newsletter = template_with_config.generate_newsletter(articles)

        assert short_description in newsletter
        assert "..." not in newsletter

    def test_description_truncation_word_boundary(self, template):
        """Test that truncation happens at word boundaries when possible."""
        from yomu.config.config import Config

        config = Config(
            openrouter_api_key="test",
            sender_email="test@gmail.com",
            sender_password="test",
            recipient_email="user@test.com",
            sources=["https://test.com"],
            frequencies=["0 9 * * *"],
            max_description_length=30,
        )

        template_with_config = HTMLTemplate(config)

        description = "This is a longer description with multiple words"
        articles = {
            "Test Source": [
                {
                    "title": "Test Article",
                    "description": description,
                }
            ]
        }

        newsletter = template_with_config.generate_newsletter(articles)

        assert "word..." not in newsletter  # Should not cut "words" to "word"
        assert "..." in newsletter
        assert "This is a longer..." in newsletter

    def test_description_empty_and_none_handling(self, template):
        """Test handling of empty and None descriptions with truncation."""
        from yomu.config.config import Config

        config = Config(
            openrouter_api_key="test",
            sender_email="test@gmail.com",
            sender_password="test",
            recipient_email="user@test.com",
            sources=["https://test.com"],
            frequencies=["0 9 * * *"],
            max_description_length=50,
        )

        template_with_config = HTMLTemplate(config)

        articles = {
            "Test Source": [
                {
                    "title": "Article with None description",
                    "description": None,
                },
                {
                    "title": "Article with empty description",
                    "description": "",
                },
            ]
        }

        newsletter = template_with_config.generate_newsletter(articles)

        assert "Article with None description" in newsletter
        assert "Article with empty description" in newsletter
        assert newsletter.count('<div class="article-description">') == 0

    def test_description_html_escaping_preserved_after_truncation(self, template):
        """Test that HTML escaping is preserved after truncation."""
        from yomu.config.config import Config

        config = Config(
            openrouter_api_key="test",
            sender_email="test@gmail.com",
            sender_password="test",
            recipient_email="user@test.com",
            sources=["https://test.com"],
            frequencies=["0 9 * * *"],
            max_description_length=50,
        )

        template_with_config = HTMLTemplate(config)

        description_with_html = "Description with <script>alert('xss')</script> and & symbols that should be very long"
        articles = {
            "Test Source": [
                {
                    "title": "Test Article",
                    "description": description_with_html,
                }
            ]
        }

        newsletter = template_with_config.generate_newsletter(articles)

        assert "<script>" in newsletter  # HTML is not escaped in descriptions
        assert "..." in newsletter

    def test_template_config_integration(self, template):
        """Test that HTMLTemplate properly integrates with Config object."""
        from yomu.config.config import Config

        config = Config(
            openrouter_api_key="test",
            sender_email="test@gmail.com",
            sender_password="test",
            recipient_email="user@test.com",
            sources=["https://test.com"],
            frequencies=["0 9 * * *"],
            max_description_length=100,
        )

        template_with_config = HTMLTemplate(config)

        assert hasattr(template_with_config, "config")
        assert template_with_config.config.max_description_length == 100
