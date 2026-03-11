from flask import render_template, redirect, url_for, flash, request, session, current_app
from . import auth_bp
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, logout_user
from ..models import User, Folder
from ..extensions import db
from sqlalchemy import or_

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
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
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
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
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))