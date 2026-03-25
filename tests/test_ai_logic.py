from app.services.ai_insight_service import AIInsightService


def test_anomaly_detection_flags_large_drop():
    history = [10000, 10100, 9900, 10050, 9950]
    result = AIInsightService.detect_anomaly(history, 5000)
    assert result["is_anomalous"] is True


def test_duplicate_detection_by_title_similarity(app):
    from app.extensions import db
    from app.models import User, TrackedProduct
    from app.utils.helpers import normalize_title

    with app.app_context():
        user = User.query.filter_by(email="user@example.com").first()
        product = TrackedProduct(
            user_id=user.id,
            source_site="amazon",
            product_url="https://amazon.in/dp/B000000001",
            normalized_url="https://amazon.in/dp/B000000001",
            title="Apple iPhone 15 Pro 128GB",
            normalized_title=normalize_title("Apple iPhone 15 Pro 128GB"),
        )
        db.session.add(product)
        db.session.commit()

        matches = AIInsightService.find_possible_duplicates(
            user,
            "https://amazon.in/dp/B999999999",
            "Apple iPhone 15 Pro 128 GB",
            "amazon"
        )
        assert matches
        assert matches[0]["score"] >= 88
