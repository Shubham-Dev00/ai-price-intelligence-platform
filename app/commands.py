import click
from .extensions import db


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        """Create database tables directly from models."""
        db.create_all()
        click.echo("Database tables created successfully.")

    @app.cli.command("reset-db")
    @click.confirmation_option(prompt="This will drop and recreate all tables. Continue?")
    def reset_db():
        """Drop and recreate all database tables."""
        db.drop_all()
        db.create_all()
        click.echo("Database reset successfully.")

    @app.cli.command("seed-db")
    def seed_db():
        """Seed demo data."""
        from seed import seed_database
        seed_database()
        click.echo("Seed data created successfully.")