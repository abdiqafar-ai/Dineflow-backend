from enum import Enum
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from . import db   # use the shared `db` from models/__init__.py


class RoleEnum(str, Enum):
    CUSTOMER = "CUSTOMER"
    WAITER   = "WAITER"
    CHEF     = "CHEF"
    ADMIN    = "ADMIN"
    CASHIER  = "CASHIER"


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id                = db.Column(db.Integer, primary_key=True)
    full_name         = db.Column(db.String(150), nullable=False)
    email             = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email_notifications = db.Column(db.Boolean, default=True)
    password_hash     = db.Column(db.String(256))
    role              = db.Column(db.Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)
    avatar_url        = db.Column(db.String(255), default="/static/avatars/default.png")
    status            = db.Column(db.String(20), default="active")    # active, suspended, banned
    suspension_ends_at= db.Column(db.DateTime, nullable=True)
    reset_token       = db.Column(db.String(100), nullable=True, index=True)
    is_google_account = db.Column(db.Boolean, default=False)
    last_login        = db.Column(db.DateTime, nullable=True)
    gender            = db.Column(db.String(10), nullable=True)

    # One User → Many Reservations
    reservations = db.relationship(
        'Reservation',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    sent_notifications = db.relationship('Notification', 
        foreign_keys='Notification.sender_id',
        backref='sender_ref',
        lazy='dynamic')
    
    received_notifications = db.relationship('Notification', 
        foreign_keys='Notification.recipient_id',
        backref='recipient_ref',
        lazy='dynamic')

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role.value,
            "avatar_url": self.avatar_url,
            "status": self.status,
            "suspension_ends_at": self.suspension_ends_at.isoformat() if self.suspension_ends_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "gender": self.gender,
            "is_google_account": self.is_google_account,
        }
