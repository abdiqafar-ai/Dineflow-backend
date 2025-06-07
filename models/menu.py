from datetime import datetime, timedelta
from . import db  # Import the shared db instance

class MenuCategory(db.Model):
    __tablename__ = 'menu_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_order = db.Column(db.Integer, default=0)
    parent_id = db.Column(db.Integer, db.ForeignKey('menu_categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    menu_items = db.relationship('MenuItem', backref='category', lazy=True)
    children = db.relationship('MenuCategory', backref=db.backref('parent', remote_side=[id]))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "menu_items": [item.to_dict() for item in self.menu_items if item.is_available],
            "subcategories": [child.to_dict() for child in self.children]
        }


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

    # Use a string for the relationship target to avoid circular import issues
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


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    waiter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    table_id = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=True)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_completion = db.Column(db.DateTime, nullable=True)

    items = db.relationship('OrderItem', backref='order', lazy=True)
    payment = db.relationship('Payment', backref='order', uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "waiter_id": self.waiter_id,
            "table_id": self.table_id,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "items": [item.to_dict() for item in self.items],
            "payment": self.payment.to_dict() if self.payment else None
        }

    def update_estimation(self):
        """Update the estimated completion time based on the order items."""
        if self.items:
            max_preparation_time = max(item.menu_item.preparation_time for item in self.items)
            self.estimated_completion = self.created_at + timedelta(minutes=max_preparation_time)
        else:
            self.estimated_completion = self.created_at

    def __repr__(self):
        return f'<Order {self.id}>'