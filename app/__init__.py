from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")  # Allow all origins for development

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    # Register blueprints
    from app.routes import auth, main, trading, ai
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(trading.bp)
    app.register_blueprint(ai.bp)

    # Import socket events here to avoid circular imports
    from app import socket_events

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
