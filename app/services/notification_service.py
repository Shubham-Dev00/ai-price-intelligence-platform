import smtplib
from email.mime.text import MIMEText
from flask import current_app
from app.extensions import db
from app.models import AlertEvent


class NotificationService:
    @staticmethod
    def send_price_alert(product, current_price, priority_score):
        user = product.user
        destination = user.email
        subject = f"Price alert: {product.title[:80]}"
        body = (
            f"Current price: ₹{current_price}\n"
            f"Target price: ₹{product.target_price}\n"
            f"Priority score: {priority_score}\n"
            f"URL: {product.product_url}"
        )
        provider = current_app.config.get("MAIL_PROVIDER", "smtp")
        if provider == "smtp":
            NotificationService._send_via_smtp(destination, subject, body)
        elif provider == "sendgrid":
            current_app.logger.info("SendGrid placeholder used for %s", destination)
        else:
            current_app.logger.warning("Unknown mail provider configured: %s", provider)

        event = AlertEvent(
            product_id=product.id,
            price_at_alert=current_price,
            target_price=product.target_price,
            priority_score=priority_score,
            channel="email",
            status="sent",
            message=body,
        )
        db.session.add(event)

    @staticmethod
    def _send_via_smtp(destination, subject, body):
        server = current_app.config.get("MAIL_SERVER")
        username = current_app.config.get("MAIL_USERNAME")
        password = current_app.config.get("MAIL_PASSWORD")
        if not all([server, username, password]):
            current_app.logger.warning("SMTP settings are incomplete. Email skipped for %s", destination)
            return

        message = MIMEText(body)
        message["Subject"] = subject
        message["From"] = current_app.config["MAIL_DEFAULT_SENDER"]
        message["To"] = destination

        with smtplib.SMTP(server, current_app.config["MAIL_PORT"]) as smtp:
            if current_app.config["MAIL_USE_TLS"]:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(message)
