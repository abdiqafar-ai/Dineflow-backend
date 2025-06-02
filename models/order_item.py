from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

db = SQLAlchemy()

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.String(255), nullable=True)
    chef_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    chef = db.relationship('User', foreign_keys=[chef_id])

    def to_dict(self):
        return {
            "id": self.id,
            "menu_item": self.menu_item.to_dict() if self.menu_item else None,
            "quantity": self.quantity,
            "status": self.status,
            "notes": self.notes,
            "chef": self.chef.full_name if self.chef else None
        }
