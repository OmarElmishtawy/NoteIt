"""Shared pytest fixtures for NoteIt tests."""

import os
import pytest
from app import create_app, db
from app.models import User, Folder
from werkzeug.security import generate_password_hash

# --- URL constants ---
URL_LOGIN = "/login"
URL_REGISTER = "/register"
URL_LOGOUT = "/logout"
URL_DASHBOARD = "/dashboard"

# --- Flash message constants ---
MSG_INVALID_CREDENTIALS = b"Invalid username or password."
MSG_EMAIL_EXISTS = b"Email already exists."
MSG_USERNAME_EXISTS = b"Username already exists."
MSG_INVALID_EMAIL = b"Invalid email address."
MSG_LOGGED_OUT = b"You have been logged out."
MSG_ACCOUNT_CREATED = b"Account created successfully."


@pytest.fixture
def app():
    """Create and configure a Flask app for testing with an in-memory database."""
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    """Create a test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture
def registered_user(app):
    """
    Create a user in the DB with a default Personal folder. Return credentials.
    Use when a test needs a pre-existing user (e.g. login, folder/note flows).
    """
    with app.app_context():
        username = "testuser"
        email = "testuser@example.com"
        password = "testpassword"
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_active=True,
        )
        db.session.add(user)
        personal = Folder(name="Personal", owner=user)
        db.session.add(personal)
        db.session.commit()
        yield {"username": username, "email": email, "password": password}
