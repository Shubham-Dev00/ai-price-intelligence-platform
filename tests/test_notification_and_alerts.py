from datetime import datetime
from app.models import User, TrackedProduct, PriceSnapshot
from app.services.ai_insight_service import AIInsightService


def test_alert_priority_positive_for_deep_discount(app):
    with app.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        product = TrackedProduct(
            user_id=user.id,
            source_site="amazon",
            product_url="https://amazon.in/dp/B000000001",
            normalized_url="https://amazon.in/dp/B000000001",
            title="Test Device",
            normalized_title="test device",
            target_price=9000,
            latest_price=8500,
        )
        from app.extensions import db
        db.session.add(product)
        db.session.flush()
        for price in [10000, 9800, 9600]:
            db.session.add(PriceSnapshot(product_id=product.id, price=price, source_site="amazon"))
        db.session.commit()

        score = AIInsightService.calculate_alert_priority(product, 8500)
        assert score > 0
