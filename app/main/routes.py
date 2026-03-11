from flask import render_template, redirect, url_for
from . import main_bp
from flask_login import login_required, current_user
from ..models import Folder
from ..extensions import db


@main_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template("main.html")


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # ensure default Personal folder exists for the user
    folders = Folder.query.filter_by(user_id=current_user.id).order_by(Folder.created_at.asc()).all()
    return render_template("dashboard.html", folders=folders)


@main_bp.route('/search')
def search_notes():
    from flask import request
    query = request.args.get('q', '')
    notes = [{'id': 1, 'title': 'Note 1', 'content': 'Content 1'}] if query else []
    return render_template("main/search_notes.html", query=query, notes=notes)