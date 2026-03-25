from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.services.analytics_service import AnalyticsService
from app.models import TrackedProduct, PriceSnapshot, ScrapeAttempt

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/")
@login_required
def home():
    kpis = AnalyticsService.get_dashboard_kpis(current_user)
    recent_products = current_user.products.order_by(TrackedProduct.updated_at.desc()).limit(10).all()
    return render_template("dashboard/home.html", kpis=kpis, recent_products=recent_products)
