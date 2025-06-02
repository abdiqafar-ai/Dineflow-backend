from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class RoleEnum(str, Enum):
    CUSTOMER = "Customer"
    WAITER = "Waiter"
    CHEF = "Chef"
    ADMIN = "Admin"
    CASHIER = "Cashier"

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='Customer')
    avatar_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="active",server_default="active")
    is_google_account = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ← Add this line:
    suspension_ends_at = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": (self.role or "").lower(),
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

