from unittest.mock import patch
from app.models import TrackedProduct, ScrapeAttempt, User
from app.services.product_service import ProductService
from app.services.scraper_service import ScrapeResult


def test_manual_fallback_creates_product_when_blocked(app):
    with app.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        blocked_result = ScrapeResult(
            success=False,
            source_site="flipkart",
            parser_used="flipkart_bs4",
            error_message="Flipkart returned a blocked/anti-bot page.",
            metadata={"blocked": True},
        )
        with patch("app.services.product_service.ScraperService.scrape_product", return_value=blocked_result):
            product, scrape_result, duplicates = ProductService.add_product_for_user(
                user,
                "https://www.flipkart.com/item/p/itm123?pid=ABC",
                title_override="boat airdopes 219",
                target_price=999,
                is_tracking_enabled=True,
            )

        assert product is not None
        assert scrape_result.success is False
        assert product.last_status == "scrape_blocked"
        assert product.latest_price is None
        assert duplicates == []
        attempt = ScrapeAttempt.query.filter_by(product_id=product.id).first()
        assert attempt is not None
        assert attempt.status == "failed"


def test_manual_fallback_requires_title_override(app):
    with app.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        blocked_result = ScrapeResult(
            success=False,
            source_site="amazon",
            parser_used="amazon_bs4",
            error_message="Amazon returned a blocked/anti-bot page.",
            metadata={"blocked": True},
        )
        with patch("app.services.product_service.ScraperService.scrape_product", return_value=blocked_result):
            product, scrape_result, duplicates = ProductService.add_product_for_user(
                user,
                "https://www.amazon.in/dp/B000000001",
                title_override=None,
                target_price=5000,
                is_tracking_enabled=True,
            )

        assert product is None
        assert scrape_result.success is False
