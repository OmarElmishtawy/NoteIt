"""Unit tests for authentication routes: login, register, logout."""

import pytest
from app.models import User, Folder
from app import db

from app.tests.conftest import (
    URL_LOGIN,
    URL_REGISTER,
    URL_LOGOUT,
    URL_DASHBOARD,
    MSG_INVALID_CREDENTIALS,
    MSG_EMAIL_EXISTS,
    MSG_USERNAME_EXISTS,
    MSG_INVALID_EMAIL,
    MSG_LOGGED_OUT,
    MSG_ACCOUNT_CREATED,
)


# --- Login ---


def test_login_page_renders(client):
    """GET /login returns 200 and shows the login form."""
    response = client.get(URL_LOGIN)
    assert response.status_code == 200
    assert b"Log in" in response.data


def test_login_with_valid_credentials_username(client, app, registered_user):
    """POST /login with valid username and password redirects to dashboard."""
    data = {"username": registered_user["username"], "password": registered_user["password"]}
    response = client.post(URL_LOGIN, data=data)
    assert response.status_code == 302
    assert URL_DASHBOARD in response.location


def test_login_with_valid_credentials_email(client, app, registered_user):
    """POST /login with valid email (as identifier) and password redirects to dashboard."""
    data = {"username": registered_user["email"], "password": registered_user["password"]}
    response = client.post(URL_LOGIN, data=data)
    assert response.status_code == 302
    assert URL_DASHBOARD in response.location


@pytest.mark.parametrize("username,password", [
    ("testuser", "wrongpassword"),      # wrong password
    ("nonexistent", "anypassword"),     # nonexistent user
    ("", ""),                           # both empty
    ("testuser", ""),                   # empty password
    ("", "testpassword"),               # empty username
])
def test_login_with_invalid_credentials(client, app, registered_user, username, password):
    """POST /login with invalid credentials shows error and stays on login page."""
    if username == "testuser":
        username = registered_user["username"]
    if password == "testpassword":
        password = registered_user["password"]
    data = {"username": username, "password": password}
    response = client.post(URL_LOGIN, data=data)
    assert response.status_code == 200
    assert MSG_INVALID_CREDENTIALS in response.data


def test_authenticated_user_redirected_from_login(client, app, registered_user):
    """Logged-in user visiting GET /login is redirected to dashboard."""
    client.post(URL_LOGIN, data=registered_user)
    response = client.get(URL_LOGIN)
    assert response.status_code == 302
    assert URL_DASHBOARD in response.location


# --- Register ---


def test_register_page_renders(client):
    """GET /register returns 200 and shows the registration form."""
    response = client.get(URL_REGISTER)
    assert response.status_code == 200
    assert b"Register" in response.data or b"Create an account" in response.data


def test_register_with_valid_credentials(client, app):
    """POST /register with valid data redirects to login and creates user and Personal folder."""
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "securepass123",
    }
    response = client.post(URL_REGISTER, data=data)
    assert response.status_code == 302
    assert URL_LOGIN in response.location

    with app.app_context():
        user = User.query.filter_by(username="newuser").first()
        assert user is not None
        assert user.email == "newuser@example.com"
        folder = Folder.query.filter_by(user_id=user.id, name="Personal").first()
        assert folder is not None


def test_register_with_existing_email(client, app, registered_user):
    """POST /register with existing email shows error and does not create user."""
    data = {
        "username": "differentuser",
        "email": registered_user["email"],
        "password": "anypassword",
    }
    response = client.post(URL_REGISTER, data=data)
    assert response.status_code == 200
    assert MSG_EMAIL_EXISTS in response.data


def test_register_with_existing_username(client, app, registered_user):
    """POST /register with existing username shows error and does not create user."""
    data = {
        "username": registered_user["username"],
        "email": "different@example.com",
        "password": "anypassword",
    }
    response = client.post(URL_REGISTER, data=data)
    assert response.status_code == 200
    assert MSG_USERNAME_EXISTS in response.data


@pytest.mark.parametrize("invalid_email", [
    "notanemail",
    "missing-at.com",
    "no-tld@domain",
    "spaces in@email.com",
    "@nodomain.com",
])
def test_register_with_invalid_email(client, app, invalid_email):
    """POST /register with invalid email format shows error."""
    data = {
        "username": "test",
        "email": invalid_email,
        "password": "anypassword",
    }
    response = client.post(URL_REGISTER, data=data)
    assert response.status_code == 200
    assert MSG_INVALID_EMAIL in response.data


@pytest.mark.parametrize("field_overrides,expected_msg", [
    ({"username": "", "email": "", "password": ""}, MSG_INVALID_EMAIL),
    ({"username": "test", "email": "", "password": "pass"}, MSG_INVALID_EMAIL),
    ({"username": "test", "email": "bademail", "password": "pass"}, MSG_INVALID_EMAIL),
])
def test_register_with_empty_fields(client, app, field_overrides, expected_msg):
    """POST /register with empty or invalid required fields shows error."""
    base = {"username": "test", "email": "valid@example.com", "password": "pass"}
    data = {**base, **field_overrides}
    response = client.post(URL_REGISTER, data=data)
    assert response.status_code == 200
    assert expected_msg in response.data


def test_register_authenticated_user_redirected_from_register(client, app, registered_user):
    """Logged-in user visiting GET /register is redirected to dashboard."""
    client.post(URL_LOGIN, data=registered_user)
    response = client.get(URL_REGISTER)
    assert response.status_code == 302
    assert URL_DASHBOARD in response.location


# --- Logout ---


def test_logout(client, app, registered_user):
    """POST /logout logs the user out and redirects to login."""
    client.post(URL_LOGIN, data=registered_user)
    response = client.post(URL_LOGOUT)
    assert response.status_code == 302
    assert URL_LOGIN in response.location

    # Verify user cannot access protected page after logout
    dash_response = client.get(URL_DASHBOARD)
    assert dash_response.status_code == 302
    assert URL_LOGIN in dash_response.location
