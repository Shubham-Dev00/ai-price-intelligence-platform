import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask

from .extensions import db, migrate, login_manager, csrf
from .errors import register_error_handlers
from .routes.auth import auth_bp
from .routes.dashboard import dashboard_bp
from .routes.products import products_bp
from .routes.admin import admin_bp
from .commands import register_commands
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from .models import User
from .services.scheduler_service import init_scheduler


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def create_app(config_name=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    config_name = config_name or os.getenv("FLASK_ENV", "development")

    if isinstance(config_name, str):
        app.config.from_object(CONFIG_MAP.get(config_name, DevelopmentConfig))
    else:
        app.config.from_object(config_name)

    configure_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_commands(app)
    init_scheduler(app)

    @app.shell_context_processor
    def make_shell_context():
        from .models import (
            User,
            TrackedProduct,
            PriceSnapshot,
            AlertEvent,
            ScrapeAttempt,
            ProductInsight,
            NotificationPreference,
            AdminAuditLog,
        )
        return {
            "db": db,
            "User": User,
            "TrackedProduct": TrackedProduct,
            "PriceSnapshot": PriceSnapshot,
            "AlertEvent": AlertEvent,
            "ScrapeAttempt": ScrapeAttempt,
            "ProductInsight": ProductInsight,
            "NotificationPreference": NotificationPreference,
            "AdminAuditLog": AdminAuditLog,
        }

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "environment": config_name,
            "database": "configured",
        }, 200

    return app


def configure_logging(app):
    if app.debug or app.testing:
        return

    file_handler = RotatingFileHandler(
        app.config["LOG_DIR"] / "app.log",
        maxBytes=1_000_000,
        backupCount=5,
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Application startup")


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(admin_bp)