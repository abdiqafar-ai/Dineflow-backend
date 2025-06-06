from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
import os

from models import db, login_manager  # import from __init__.py
from models.user import User
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.table_routes import table_bp
from routes.reservation_routes import reservation_routes
# from routes.order_routes import order_bp
# from routes.reservation_routes import reservation_bp
from utils.google_oauth import init_oauth

def create_app():
    app = Flask(__name__)

    # Load config
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        app.config.from_object("config.ProductionConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    Migrate(app, db)
    CORS(app, supports_credentials=True)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(table_bp)
    app.register_blueprint(reservation_routes)
    # app.register_blueprint(order_bp)
    # app.register_blueprint(reservation_bp)

    # Initialize Google OAuth
    init_oauth(app)

    # Ensure avatar folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/avatars"), exist_ok=True)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
