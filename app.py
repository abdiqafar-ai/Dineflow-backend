import os
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables from .env file first
load_dotenv()

# Import configuration after loading environment variables
from config import DevelopmentConfig, ProductionConfig
from models import db, login_manager
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.table_routes import table_bp
from routes.reservation_routes import reservation_routes
from routes.menu_routes import menu_routes
from routes.payment_routes import payment_routes
from routes.notification_routes import notification_routes
from utils.google_oauth import init_oauth

def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Determine environment and load config
    env = os.getenv("FLASK_ENV", "development")
    app.config.from_object(
        ProductionConfig() if env == "production" else DevelopmentConfig()
    )

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
    app.register_blueprint(menu_routes)
    app.register_blueprint(payment_routes)
    app.register_blueprint(notification_routes)

    # Initialize Google OAuth
    init_oauth(app)

    # Ensure avatar folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)