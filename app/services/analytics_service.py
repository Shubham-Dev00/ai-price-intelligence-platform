from statistics import mean
from app.models import PriceSnapshot


class AnalyticsService:
    @staticmethod
    def get_price_metrics(product):
        prices = [snapshot.price for snapshot in product.price_snapshots.order_by(PriceSnapshot.captured_at.asc()).all()]
        if not prices:
            return {
                "latest": None,
                "lowest": None,
                "highest": None,
                "average": None,
                "count": 0,
            }
        return {
            "latest": prices[-1],
            "lowest": min(prices),
            "highest": max(prices),
            "average": round(mean(prices), 2),
            "count": len(prices),
        }

    @staticmethod
    def get_dashboard_kpis(user):
        products = user.products.all()
        below_target = sum(1 for p in products if p.is_below_target)
        failures = sum(1 for p in products if p.last_status == "failed")
        alerts_sent = sum(p.alert_events.count() for p in products)
        return {
            "total_tracked_products": len(products),
            "products_below_target": below_target,
            "recent_scrape_failures": failures,
            "alerts_sent": alerts_sent,
        }
