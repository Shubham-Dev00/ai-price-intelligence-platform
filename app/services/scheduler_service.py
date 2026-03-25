from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from app.models import TrackedProduct
from .product_service import ProductService

scheduler = BackgroundScheduler()


def init_scheduler(app):
    if app.config.get("USE_APSCHEDULER_FALLBACK", True) and not scheduler.running:
        scheduler.configure(timezone="UTC")


def run_price_checks(app):
    with app.app_context():
        products = TrackedProduct.query.filter_by(is_tracking_enabled=True).all()
        for product in products:
            ProductService.refresh_product(product)


def start_scheduler(app):
    if app.config.get("USE_APSCHEDULER_FALLBACK", True) and not scheduler.running:
        scheduler.add_job(
            func=lambda: run_price_checks(app),
            trigger="interval",
            minutes=app.config.get("PRICE_CHECK_INTERVAL_MINUTES", 30),
            id="price_checks",
            replace_existing=True,
        )
        scheduler.start()
        app.logger.info("APScheduler fallback started")
