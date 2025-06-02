# app.py

from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
import os

from models.user import db, User
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from utils.google_oauth import oauth, init_oauth  # import both

def create_app():
    app = Flask(__name__)

    # Load config...
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        app.config.from_object("config.ProductionConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    CORS(app, supports_credentials=True)

    login_manager = LoginManager()
    login_manager.login_view = "auth_bp.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    # **Initialize Google OAuth** (registers the 'google' client)
    init_oauth(app)

    # Ensure avatar folder exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/avatars"), exist_ok=True)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
