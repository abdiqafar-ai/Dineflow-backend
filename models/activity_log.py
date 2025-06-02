from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

db = SQLAlchemy()

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    activity_data = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.full_name if self.user else None,
            "role": self.user.role.value if self.user else None,
            "action_type": self.action_type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address
        }
