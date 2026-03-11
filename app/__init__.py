from flask import Flask
from .extensions import db, migrate, login_manager



def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import User, Note
    with app.app_context():
        db.create_all()

    from .auth import auth_bp
    from .folders import folders_bp
    from .notes import notes_bp
    from .main import main_bp

    # register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(folders_bp, url_prefix='/folders')
    app.register_blueprint(notes_bp, url_prefix='/notes')
    app.register_blueprint(main_bp)

    return app