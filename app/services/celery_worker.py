from celery import Celery
from app import create_app
from app.models import TrackedProduct
from .product_service import ProductService

celery = Celery(__name__)


def init_celery():
    app = create_app()
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = init_celery()


@celery.task
def run_price_checks_task():
    products = TrackedProduct.query.filter_by(is_tracking_enabled=True).all()
    for product in products:
        ProductService.refresh_product(product)
