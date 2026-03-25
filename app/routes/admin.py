from flask import Blueprint, render_template, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from app.models import User, TrackedProduct, ScrapeAttempt, AlertEvent, AdminAuditLog

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


@admin_bp.get("/")
@login_required
def dashboard():
    admin_required()
    data = {
        "total_users": User.query.count(),
        "total_products": TrackedProduct.query.count(),
        "successful_scrapes": ScrapeAttempt.query.filter_by(status="success").count(),
        "failed_scrapes": ScrapeAttempt.query.filter_by(status="failed").count(),
        "alerts_sent": AlertEvent.query.count(),
        "system_health": "Attention Needed" if ScrapeAttempt.query.filter_by(status="failed").count() > 10 else "Healthy",
        "recent_audits": AdminAuditLog.query.order_by(AdminAuditLog.created_at.desc()).limit(20).all(),
    }
    return render_template("admin/dashboard.html", data=data)
