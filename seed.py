from app import create_app
from app.extensions import db
from app.models import User, TrackedProduct, PriceSnapshot, NotificationPreference
from app.utils.helpers import normalize_title, normalize_url


def seed_database():
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(full_name="Admin User", email="admin@example.com", role="admin")
        admin.set_password("Admin@12345")
        db.session.add(admin)

    demo_user = User.query.filter_by(email="demo@example.com").first()
    if not demo_user:
        demo_user = User(full_name="Demo User", email="demo@example.com", role="user")
        demo_user.set_password("Demo@12345")
        db.session.add(demo_user)
        db.session.flush()

    existing_product = TrackedProduct.query.filter_by(
        user_id=demo_user.id,
        normalized_url=normalize_url("https://amazon.in/dp/B000000001"),
    ).first()

    if not existing_product:
        product = TrackedProduct(
            user_id=demo_user.id,
            source_site="amazon",
            product_url="https://amazon.in/dp/B000000001",
            normalized_url=normalize_url("https://amazon.in/dp/B000000001"),
            title="Demo Product",
            normalized_title=normalize_title("Demo Product"),
            latest_price=49999,
            target_price=45999,
            currency="INR",
            last_status="success",
            is_tracking_enabled=True,
        )
        db.session.add(product)
        db.session.flush()

        for price in [52999, 51999, 50999, 49999]:
            db.session.add(
                PriceSnapshot(
                    product_id=product.id,
                    price=price,
                    currency="INR",
                    source_site="amazon",
                )
            )

    existing_pref = NotificationPreference.query.filter_by(
        user_id=demo_user.id,
        channel="email",
    ).first()

    if not existing_pref:
        db.session.add(
            NotificationPreference(
                user_id=demo_user.id,
                channel="email",
                is_enabled=True,
                destination="demo@example.com",
            )
        )

    db.session.commit()
    print("Seed data created.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_database()