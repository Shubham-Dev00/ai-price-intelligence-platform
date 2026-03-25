import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")


def _sqlite_uri_for(filename: str = "app.db") -> str:
    return f"sqlite:///{(INSTANCE_DIR / filename).resolve().as_posix()}"


def _resolve_database_uri(raw_uri: str | None) -> str:
    """
    Makes local SQLite paths stable even if .env contains:
    - sqlite:///app.db
    - sqlite:///./app.db

    PostgreSQL / absolute SQLite URLs are left unchanged.
    """
    if not raw_uri:
        return _sqlite_uri_for("app.db")

    if raw_uri.startswith("sqlite:///./"):
        db_name = raw_uri.removeprefix("sqlite:///./")
        return _sqlite_uri_for(db_name)

    if raw_uri.startswith("sqlite:///") and not raw_uri.startswith("sqlite:////"):
        remainder = raw_uri.removeprefix("sqlite:///")
        if "/" not in remainder and "\\" not in remainder:
            return _sqlite_uri_for(remainder)

    return raw_uri


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None

    MAIL_PROVIDER = os.getenv("MAIL_PROVIDER", "smtp")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@example.com")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

    SCRAPER_TIMEOUT_SECONDS = int(os.getenv("SCRAPER_TIMEOUT_SECONDS", 12))
    SCRAPER_RETRY_COUNT = int(os.getenv("SCRAPER_RETRY_COUNT", 2))
    ENABLE_SELENIUM_FALLBACK = os.getenv("ENABLE_SELENIUM_FALLBACK", "False").lower() == "true"
    SELENIUM_REMOTE_URL = os.getenv("SELENIUM_REMOTE_URL", "http://localhost:4444/wd/hub")

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    PRICE_CHECK_INTERVAL_MINUTES = int(os.getenv("PRICE_CHECK_INTERVAL_MINUTES", 30))
    USE_APSCHEDULER_FALLBACK = os.getenv("USE_APSCHEDULER_FALLBACK", "True").lower() == "true"

    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True

    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri(os.getenv("DATABASE_URL"))


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")


class ProductionConfig(BaseConfig):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True