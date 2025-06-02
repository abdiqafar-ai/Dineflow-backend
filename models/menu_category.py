from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

db = SQLAlchemy()

class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_order = db.Column(db.Integer, default=0)
    parent_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    menu_items = db.relationship('MenuItem', backref='category', lazy=True)
    children = db.relationship('MenuCategory') 

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "menu_items": [item.to_dict() for item in self.menu_items if item.is_available],
            "subcategories": [child.to_dict() for child in self.children]
        }
