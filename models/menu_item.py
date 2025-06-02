from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

db = SQLAlchemy()

class MenuItem(db.Model):
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'))
    preparation_time = db.Column(db.Integer, default=15)
    calories = db.Column(db.Integer, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    ingredients = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order_items = db.relationship('OrderItem', backref='menu_item', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "image_url": self.image_url,
            "category_id": self.category_id,
            "is_available": self.is_available,
            "preparation_time": self.preparation_time,
            "calories": self.calories
        }
