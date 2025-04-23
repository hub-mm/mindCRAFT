from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from jinja2 import StrictUndefined
from itsdangerous import URLSafeSerializer

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'


def get_serializer():
    from flask import current_app
    return URLSafeSerializer(current_app.config['SECRET_KEY'])


def create_app(config_class=Config):
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder='static',
        template_folder='templates'
    )
    app.jinja_env.undefined = StrictUndefined
    app.config.from_object(config_class)
    app.config.from_pyfile('config.py', silent=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    from app.public.routes import public_bp
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.flashcards.routes import flashcards_bp
    from app.errors.handlers import errors_bp

    app.register_blueprint(public_bp, url_prefix='/public')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(flashcards_bp, url_prefix='/flashcards')
    app.register_blueprint(errors_bp)

    @app.shell_context_processor
    def make_shell_context():
        return dict(
            app=app,
            db=db,
        )

    return app
