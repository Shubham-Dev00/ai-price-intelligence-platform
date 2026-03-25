from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models import TrackedProduct, PriceSnapshot, ScrapeAttempt
from app.utils.helpers import detect_source_site, normalize_title, normalize_url
from .scraper_service import ScraperService
from .ai_insight_service import AIInsightService
from .notification_service import NotificationService


class ProductService:
    @staticmethod
    def _supports_manual_fallback(scrape_result, title_override):
        if not title_override:
            return False
        if scrape_result.source_site not in {"amazon", "flipkart"}:
            return False
        blocked = bool((scrape_result.metadata or {}).get("blocked"))
        return blocked or "failed to parse" in (scrape_result.error_message or "").lower()

    @staticmethod
    def add_product_for_user(user, product_url, title_override=None, target_price=None, is_tracking_enabled=True):
        normalized_url = normalize_url(product_url)
        scrape_result = ScraperService.scrape_product(product_url)
        source_site = detect_source_site(product_url)
        title_for_duplicate_check = title_override or scrape_result.title or ""
        duplicates = AIInsightService.find_possible_duplicates(user, normalized_url, title_for_duplicate_check, source_site)

        if not scrape_result.success and not ProductService._supports_manual_fallback(scrape_result, title_override):
            return None, scrape_result, duplicates

        now = datetime.utcnow()
        if scrape_result.success:
            product = TrackedProduct(
                user_id=user.id,
                source_site=source_site,
                product_url=product_url,
                normalized_url=normalized_url,
                title=title_override or scrape_result.title,
                normalized_title=normalize_title(title_override or scrape_result.title),
                target_price=target_price,
                latest_price=scrape_result.current_price,
                currency=scrape_result.currency,
                is_tracking_enabled=is_tracking_enabled,
                last_status="success",
                last_checked_at=now,
                last_success_at=now,
                last_availability=scrape_result.availability,
            )
            db.session.add(product)
            db.session.flush()

            snapshot = PriceSnapshot(
                product_id=product.id,
                price=scrape_result.current_price,
                currency=scrape_result.currency,
                availability=scrape_result.availability,
                source_site=source_site,
            )
            db.session.add(snapshot)

            attempt = ScrapeAttempt(
                product_id=product.id,
                status="success",
                http_status=scrape_result.http_status,
                scraped_price=scrape_result.current_price,
                availability=scrape_result.availability,
                parser_used=scrape_result.parser_used,
                metadata_json=scrape_result.metadata or {},
            )
            db.session.add(attempt)
        else:
            blocked = bool((scrape_result.metadata or {}).get("blocked"))
            product = TrackedProduct(
                user_id=user.id,
                source_site=source_site,
                product_url=product_url,
                normalized_url=normalized_url,
                title=title_override,
                normalized_title=normalize_title(title_override),
                target_price=target_price,
                latest_price=None,
                currency=scrape_result.currency,
                is_tracking_enabled=is_tracking_enabled,
                last_status="scrape_blocked" if blocked else "pending_manual_review",
                last_checked_at=now,
                last_failure_at=now,
                last_availability=None,
            )
            db.session.add(product)
            db.session.flush()

            attempt = ScrapeAttempt(
                product_id=product.id,
                status="failed",
                http_status=scrape_result.http_status,
                error_message=scrape_result.error_message,
                parser_used=scrape_result.parser_used,
                metadata_json=scrape_result.metadata or {},
            )
            db.session.add(attempt)
            current_app.logger.warning(
                "Created product %s using manual fallback after scrape failure: %s",
                product.id,
                scrape_result.error_message,
            )

        AIInsightService.persist_insights(product)
        db.session.commit()
        return product, scrape_result, duplicates

    @staticmethod
    def refresh_product(product):
        scrape_result = ScraperService.scrape_product(product.product_url)
        now = datetime.utcnow()
        product.last_checked_at = now

        if scrape_result.success:
            historical_prices = [s.price for s in product.price_snapshots.order_by(PriceSnapshot.captured_at.asc()).all()]
            anomaly = AIInsightService.detect_anomaly(historical_prices, scrape_result.current_price)
            snapshot = PriceSnapshot(
                product_id=product.id,
                price=scrape_result.current_price,
                currency=scrape_result.currency,
                availability=scrape_result.availability,
                source_site=product.source_site,
                is_anomalous=anomaly["is_anomalous"],
                anomaly_score=anomaly["score"],
            )
            db.session.add(snapshot)

            product.latest_price = scrape_result.current_price
            product.last_success_at = now
            product.last_availability = scrape_result.availability
            product.last_status = "success"
            product.is_below_target = bool(product.target_price and scrape_result.current_price <= product.target_price)

            if product.alert_active and not product.is_below_target:
                product.alert_active = False

            if product.is_below_target and not product.alert_active and not anomaly["is_anomalous"]:
                priority_score = AIInsightService.calculate_alert_priority(product, scrape_result.current_price)
                NotificationService.send_price_alert(product, scrape_result.current_price, priority_score)
                product.alert_active = True
                product.last_alert_sent_at = now

            AIInsightService.persist_insights(product)
            attempt = ScrapeAttempt(
                product_id=product.id,
                status="success",
                http_status=scrape_result.http_status,
                scraped_price=scrape_result.current_price,
                availability=scrape_result.availability,
                parser_used=scrape_result.parser_used,
                metadata_json={"anomaly": anomaly},
            )
            db.session.add(attempt)
        else:
            product.last_failure_at = now
            product.last_status = "scrape_blocked" if bool((scrape_result.metadata or {}).get("blocked")) else "failed"
            attempt = ScrapeAttempt(
                product_id=product.id,
                status="failed",
                http_status=scrape_result.http_status,
                error_message=scrape_result.error_message,
                parser_used=scrape_result.parser_used,
                metadata_json=scrape_result.metadata or {},
            )
            db.session.add(attempt)
            current_app.logger.warning("Scrape failed for product %s: %s", product.id, scrape_result.error_message)

        db.session.commit()
        return scrape_result
