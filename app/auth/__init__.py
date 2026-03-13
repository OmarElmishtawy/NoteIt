from flask import Blueprint, request, redirect, url_for
from flask_login import current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.before_request
def _redirect_authenticated_from_auth_pages():
    """Redirect authenticated users away from login and register pages.

    If a logged-in user visits /login or /register, sends them to the dashboard
    instead of showing the auth form.

    Returns:
        werkzeug.wrappers.Response: Redirect to main.dashboard if the user is
            authenticated and the endpoint is auth.login or auth.register.
        None: If the request should proceed normally.
    """
    endpoint = request.endpoint or ""
    if current_user.is_authenticated and endpoint in ("auth.login", "auth.register"):
        return redirect(url_for("main.dashboard"))

from . import routes