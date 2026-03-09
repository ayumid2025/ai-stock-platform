from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirect to login page if not authenticated
    login_manager.login_message = 'Please log in to access this page.'
    from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

    # Register blueprints
    from app.routes import auth, main, trading, ai
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(trading.bp)
    app.register_blueprint(ai.bp)

    # Create database tables (for development)
    with app.app_context():
        db.create_all()

    return app
