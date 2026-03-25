from wsgi import app
from app.services.scheduler_service import start_scheduler

if __name__ == "__main__":
    start_scheduler(app)
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))