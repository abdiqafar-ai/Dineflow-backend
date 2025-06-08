from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from . import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    cashier_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(100), nullable=True, unique=True)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)
    tip_amount = db.Column(db.Float, default=0.0)
    tax_amount = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)

    cashier = db.relationship('User', backref='payments', foreign_keys=[cashier_id])

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "cashier_id": self.cashier_id,  # Just show ID instead of name
            "amount": self.amount,
            "method": self.method,
            "status": self.status,
            "transaction_id": self.transaction_id,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "tip_amount": self.tip_amount,
            "tax_amount": self.tax_amount,
            "discount": self.discount
        }
    def verify_payment(self):
        """Verify payment status with payment processor"""
        if self.method == 'mpesa':
            return verify_mpesa_payment(self.transaction_id)
        elif self.method in ['credit_card', 'debit_card']:
            return verify_card_payment(self.transaction_id)
        return True  # For cash payments

        # Payment verification stubs
def verify_mpesa_payment(transaction_id):
            # In real implementation, check with M-Pesa API
            return True

def verify_card_payment(transaction_id):
            # In real implementation, check with payment gateway
            return True