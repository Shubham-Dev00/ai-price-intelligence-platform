from statistics import mean, pstdev
from rapidfuzz import fuzz
from app.models import ProductInsight, PriceSnapshot
from app.utils.helpers import normalize_title


class AIInsightService:
    @staticmethod
    def detect_anomaly(historical_prices, new_price):
        if len(historical_prices) < 3:
            return {"is_anomalous": False, "score": 0.0, "reason": "Insufficient history"}
        avg = mean(historical_prices)
        deviation = pstdev(historical_prices) or 1.0
        z_score = abs((new_price - avg) / deviation)
        rolling_deviation = abs(new_price - avg) / avg if avg else 0
        is_anomalous = z_score >= 2.5 or rolling_deviation >= 0.35
        return {
            "is_anomalous": is_anomalous,
            "score": round(max(z_score, rolling_deviation * 10), 2),
            "reason": "Price deviates significantly from baseline" if is_anomalous else "Within expected range",
        }

    @staticmethod
    def generate_trend_insights(product):
        snapshots = product.price_snapshots.order_by(PriceSnapshot.captured_at.asc()).all()
        history = [s.price for s in snapshots]
        if len(history) < 2:
            return ["Not enough price history yet to generate trend insights."]

        avg = mean(history)
        latest = history[-1]
        lowest = min(history)
        highest = max(history)
        insights = []

        recent_window = history[-5:] if len(history) >= 5 else history
        recent_range = max(recent_window) - min(recent_window)
        if avg and recent_range / avg < 0.05:
            insights.append("Price has been relatively stable in the recent observation window.")
        else:
            insights.append("Frequent fluctuations have been detected across recent price checks.")

        if latest <= lowest * 1.03:
            insights.append("Current price is near the historical low, which may be a favorable buying opportunity.")

        if product.target_price and avg and product.target_price < avg * 0.75:
            insights.append("Configured target price may be unrealistic compared with recent average pricing.")

        if latest < avg:
            insights.append("Current price is below the historical average trend.")
        else:
            insights.append("Current price is above the historical average trend.")

        return insights

    @staticmethod
    def calculate_alert_priority(product, current_price):
        target = product.target_price or current_price
        snapshots = product.price_snapshots.order_by(PriceSnapshot.captured_at.asc()).all()
        history = [s.price for s in snapshots] or [current_price]
        avg = mean(history)
        min_price = min(history)
        pct_drop_to_target = ((target - current_price) / target) * 100 if target else 0
        rarity_bonus = 20 if current_price <= min_price else 0
        below_average_bonus = ((avg - current_price) / avg) * 100 if avg else 0
        activity_bonus = min(len(history), 30)
        score = max(0, pct_drop_to_target) + max(0, below_average_bonus) + rarity_bonus + activity_bonus
        return round(score, 2)

    @staticmethod
    def find_possible_duplicates(user, normalized_url, title, source_site):
        normalized_new_title = normalize_title(title)
        candidates = []
        for product in user.products.all():
            score = fuzz.token_set_ratio(normalized_new_title, product.normalized_title)
            if product.normalized_url == normalized_url:
                candidates.append({"product_id": product.id, "reason": "Exact normalized URL match", "score": 100})
            elif product.source_site == source_site and score >= 88:
                candidates.append({"product_id": product.id, "reason": "Strong fuzzy title match", "score": score})
        return sorted(candidates, key=lambda x: x["score"], reverse=True)

    @staticmethod
    def persist_insights(product):
        insights = AIInsightService.generate_trend_insights(product)
        ProductInsight.query.filter_by(product_id=product.id).delete()
        for text in insights:
            entry = ProductInsight(
                product_id=product.id,
                insight_type="trend_summary",
                summary=text,
            )
            from app.extensions import db
            db.session.add(entry)
        return insights


class OptionalLLMSummaryHook:
    def summarize_weekly(self, product_summaries):
        return {
            "enabled": False,
            "message": "LLM summary hook is intentionally decoupled and disabled by default.",
            "payload_preview": product_summaries,
        }
