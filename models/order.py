from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from . import db

db = SQLAlchemy()

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    waiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    estimated_completion = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    payments = db.relationship('Payment', backref='order', lazy=True)

    @property
    def total_amount(self):
        return sum(item.quantity * item.menu_item.price for item in self.order_items)

    def update_estimation(self):
        if not self.order_items:
            return
        max_prep = max(item.menu_item.preparation_time for item in self.order_items)
        self.estimated_completion = datetime.utcnow() + timedelta(minutes=max_prep)

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.to_dict() if self.user else None,
            "table": self.table.to_dict() if self.table else None,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "total_amount": self.total_amount,
            "order_items": [item.to_dict() for item in self.order_items],
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None
        }
