from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, UniqueConstraint, func
from .extensions import db


class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"


class SourceSiteEnum(str, Enum):
    AMAZON = "amazon"
    FLIPKART = "flipkart"
    UNKNOWN = "unknown"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=RoleEnum.USER.value)
    is_active_user = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    products = db.relationship("TrackedProduct", back_populates="user", lazy="dynamic")
    notification_preferences = db.relationship(
        "NotificationPreference", back_populates="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class TrackedProduct(db.Model):
    __tablename__ = "tracked_products"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source_site = db.Column(db.String(50), nullable=False, index=True)
    product_url = db.Column(db.Text, nullable=False)
    normalized_url = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(500), nullable=False)
    normalized_title = db.Column(db.String(500), nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="INR")
    latest_price = db.Column(db.Float, nullable=True)
    target_price = db.Column(db.Float, nullable=True)
    last_checked_at = db.Column(db.DateTime, nullable=True)
    last_success_at = db.Column(db.DateTime, nullable=True)
    last_failure_at = db.Column(db.DateTime, nullable=True)
    last_availability = db.Column(db.String(100), nullable=True)
    last_status = db.Column(db.String(50), nullable=False, default="pending")
    is_tracking_enabled = db.Column(db.Boolean, nullable=False, default=True)
    is_below_target = db.Column(db.Boolean, nullable=False, default=False)
    alert_active = db.Column(db.Boolean, nullable=False, default=False)
    last_alert_sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="products")
    price_snapshots = db.relationship("PriceSnapshot", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")
    alert_events = db.relationship("AlertEvent", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")
    scrape_attempts = db.relationship("ScrapeAttempt", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")
    insights = db.relationship("ProductInsight", back_populates="product", lazy="dynamic", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "normalized_url", name="uq_user_normalized_url"),
        Index("ix_products_user_status", "user_id", "is_tracking_enabled", "last_status"),
    )


class PriceSnapshot(db.Model):
    __tablename__ = "price_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("tracked_products.id"), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default="INR")
    availability = db.Column(db.String(100), nullable=True)
    source_site = db.Column(db.String(50), nullable=False)
    is_anomalous = db.Column(db.Boolean, nullable=False, default=False)
    anomaly_score = db.Column(db.Float, nullable=True)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    product = db.relationship("TrackedProduct", back_populates="price_snapshots")

    __table_args__ = (
        Index("ix_snapshot_product_captured", "product_id", "captured_at"),
    )


class AlertEvent(db.Model):
    __tablename__ = "alert_events"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("tracked_products.id"), nullable=False, index=True)
    alert_type = db.Column(db.String(50), nullable=False, default="price_below_target")
    price_at_alert = db.Column(db.Float, nullable=False)
    target_price = db.Column(db.Float, nullable=True)
    priority_score = db.Column(db.Float, nullable=True)
    channel = db.Column(db.String(30), nullable=False, default="email")
    status = db.Column(db.String(30), nullable=False, default="sent")
    message = db.Column(db.Text, nullable=True)
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    product = db.relationship("TrackedProduct", back_populates="alert_events")


class ScrapeAttempt(db.Model):
    __tablename__ = "scrape_attempts"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("tracked_products.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False)
    http_status = db.Column(db.Integer, nullable=True)
    scraped_price = db.Column(db.Float, nullable=True)
    availability = db.Column(db.String(100), nullable=True)
    parser_used = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    product = db.relationship("TrackedProduct", back_populates="scrape_attempts")


class ProductInsight(db.Model):
    __tablename__ = "product_insights"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("tracked_products.id"), nullable=False, index=True)
    insight_type = db.Column(db.String(50), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=True)
    metadata_json = db.Column(db.JSON, nullable=True)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    product = db.relationship("TrackedProduct", back_populates="insights")


class NotificationPreference(db.Model):
    __tablename__ = "notification_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    channel = db.Column(db.String(30), nullable=False, default="email")
    is_enabled = db.Column(db.Boolean, nullable=False, default=True)
    destination = db.Column(db.String(255), nullable=True)
    quiet_hours_start = db.Column(db.String(5), nullable=True)
    quiet_hours_end = db.Column(db.String(5), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="notification_preferences")


class AdminAuditLog(db.Model):
    __tablename__ = "admin_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


def log_admin_action(actor_user_id, action, entity_type, entity_id=None, details=None):
    entry = AdminAuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        details=details or {},
    )
    db.session.add(entry)
