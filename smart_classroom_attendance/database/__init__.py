"""Database package initialization and SQLAlchemy instance.
Provides an `init_app(app)` helper to bind the Flask app and create tables.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    """Initialize the database with the given Flask app.
    This separates DB creation from model imports to avoid circular imports.
    """
    db.init_app(app)
    with app.app_context():
        db.create_all()

