from flask import render_template, redirect, url_for, flash, request, session, current_app
from . import auth_bp
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user
from ..models import User, Folder
from ..extensions import db
from sqlalchemy import or_
import re

def validate_email(email):
    """Check if the given string is a valid email address format.

    Uses a standard regex pattern to validate email structure (local@domain.tld).
    Does not verify that the email exists or is deliverable.

    Args:
        email: The string to validate as an email address. Can be None or empty.

    Returns:
        True if the email matches the expected format, False otherwise.
    """
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return False
    return True


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user authentication via username or email.

    GET: Render the login form.
    POST: Authenticate the user with the provided credentials. Accepts username
    or email as the identifier (both are tried). On success, redirects to the
    dashboard or the `next` query parameter if present. On failure, re-renders
    the form with an error message.

    Returns:
        On GET or failed POST: Rendered login form (HTML response).
        On successful POST: Redirect to dashboard or `next` URL.
    """
    if request.method == 'POST':
        identifier = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter(or_(User.username == identifier, User.email == identifier)).first()
        # stored hash is in password_hash column
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_page = request.args.get("next")
            return redirect(next_page or url_for("main.dashboard"))
        flash('Invalid username or password.', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle new user registration.

    GET: Render the registration form.
    POST: Create a new user account. Validates email format and ensures
    username and email are unique. Creates a default "Personal" folder
    for the new user. On success, redirects to the login page.

    Returns:
        On GET or failed POST: Rendered registration form (HTML response).
        On successful POST: Redirect to login page.

    Raises:
        Does not raise; validation errors are surfaced via flash messages.
    """
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        if not validate_email(email):
            flash('Invalid email address.', 'error')
            return render_template('auth/register.html')
        password = request.form.get('password')
        password_hash = generate_password_hash(password)
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('auth/register.html')
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('auth/register.html')
        user = User(username=username, email=email, password_hash=password_hash, is_active=True)
        # create default Personal folder for the new user
        personal = Folder(name='Personal', owner=user)
        db.session.add(user)
        db.session.add(personal)
        db.session.commit()
        flash('Account created successfully.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out the current user and clear their session.

    Requires the user to be logged in. Clears the Flask-Login session and
    redirects to the login page.

    Returns:
        Redirect response to the login page.
    """
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))