from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

from .user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))