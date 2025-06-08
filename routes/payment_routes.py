from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from models import db, Payment
from flask_login import login_required, current_user
import random
import string

payment_routes = Blueprint("payment_routes", __name__, url_prefix="/api/payments")

# --------------------- GET THE LIST OF payments ----------------
@payment_routes.route("/", methods=["GET"])
@payment_routes.route("", methods=["GET"])
@login_required
def get_payments():
    try:
        payments = Payment.query.all()
        return jsonify([payment.to_dict() for payment in payments])
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error: " + str(e)}), 500

# ----------------------------------GET A SPECIFIC payment----------
@payment_routes.route("/<int:payment_id>", methods=["GET"])
@payment_routes.route("/<int:payment_id>/", methods=["GET"])
@login_required
def get_payment(payment_id):
    try:
        payment = Payment.query.get_or_404(payment_id)
        return jsonify(payment.to_dict())
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error: " + str(e)}), 500

# ------------------------CREATE A payment--------------------
@payment_routes.route("/", methods=["POST"])
@payment_routes.route("", methods=["POST"])
@login_required
def create_payment():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['order_id', 'amount', 'method']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
        
    # Validate payment method
    allowed_methods = ['cash', 'mpesa', 'credit_card', 'debit_card']
    if data['method'] not in allowed_methods:
        return jsonify({"error": "Invalid payment method"}), 400

    try:
        payment = Payment(
            order_id=data["order_id"],
            cashier_id=current_user.id,
            amount=data["amount"],
            method=data["method"],
            status="pending",
            tip_amount=data.get("tip_amount", 0.0),
            tax_amount=data.get("tax_amount", 0.0),
            discount=data.get("discount", 0.0)
        )
        
        db.session.add(payment)
        db.session.commit()
        
        # Process payment after successful creation
        success = process_payment(payment)
        if success:
            payment.status = 'completed'
        else:
            payment.status = 'failed'
        
        db.session.commit()
        
        return jsonify(payment.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# ---------------------------UPDATE A payment------------
@payment_routes.route("/<int:payment_id>", methods=["PUT"])
@payment_routes.route("/<int:payment_id>/", methods=["PUT"])
@login_required
def update_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    data = request.get_json()
    
    # Prevent modifying completed payments
    if payment.status == 'completed':
        return jsonify({"error": "Cannot modify completed payment"}), 400

    try:
        # Only allow updating specific fields
        allowed_fields = ['amount', 'tip_amount', 'tax_amount', 'discount']
        for field in allowed_fields:
            if field in data:
                setattr(payment, field, data[field])
        
        db.session.commit()
        return jsonify(payment.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    

@payment_routes.route("/<int:payment_id>/adjust", methods=["POST"])
@login_required
def adjust_payment(payment_id):
    original = Payment.query.get_or_404(payment_id)
    data = request.get_json()
    
    # Create adjustment transaction
    adjustment = Payment(
        order_id=original.order_id,
        cashier_id=current_user.id,
        amount=-data.get("adjustment_amount", 0),
        method="adjustment",
        status="completed",
        parent_payment_id=payment_id,
        notes=data.get("reason", "Payment adjustment")
    )
    
    db.session.add(adjustment)
    db.session.commit()
    return jsonify(adjustment.to_dict()), 201

# ------------------------DELETE A payment----------------------
@payment_routes.route("/<int:payment_id>", methods=["DELETE"])
@payment_routes.route("/<int:payment_id>/", methods=["DELETE"])
@login_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    
    # Prevent deleting completed payments
    if payment.status == 'completed':
        return jsonify({"error": "Cannot delete completed payment"}), 400
        
    try:
        db.session.delete(payment)
        db.session.commit()
        return jsonify({"message": "Payment deleted"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 500

# ------------------------PAYMENT PROCESSING--------------------
def process_payment(payment):
    """Process payment through appropriate gateway"""
    try:
        if payment.method == "mpesa":
            return process_mpesa_payment(payment)
        elif payment.method in ["credit_card", "debit_card"]:
            return process_card_payment(payment)
        elif payment.method == "cash":
            return True  # Cash payments always succeed
        return False
    except Exception:
        return False

def process_mpesa_payment(payment):
    """Process M-Pesa payment and generate transaction ID"""
    # In production: Call M-Pesa API and get real transaction ID
    payment.transaction_id = f"MPESA_{random.randint(100000, 999999)}"
    # Simulate processing delay
    return True

def process_card_payment(payment):
    """Process card payment and generate transaction ID"""
    # In production: Call payment gateway API
    payment.transaction_id = f"CARD_{''.join(random.choices(string.ascii_uppercase + string.digits, k=12))}"
    # Simulate processing delay
    return True