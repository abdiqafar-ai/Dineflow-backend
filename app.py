from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()  # Load variables from .env

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    db.init_app(app)

    @app.route("/")
    def index():
        return "Hello, DineFlow with Neon PostgreSQL!"

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
