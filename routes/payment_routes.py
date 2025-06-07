from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from models import db, Payment
from flask_login import login_required, current_user

payment_routes = Blueprint("payment_routes", __name__, url_prefix="/api/payments")

#--------------------- GET THE LIST OF payments ----------------
@payment_routes.route("/", methods=["GET"])
@payment_routes.route("", methods=["GET"])
@login_required
def get_payments():
    payments = Payment.query.all()
    return jsonify([payment.to_dict() for payment in payments])

# ----------------------------------GET A SPECFIC payments----------
@payment_routes.route("/<int:payment_id>", methods=["GET"])
@payment_routes.route("/<int:payment_id>/", methods=["GET"])
@login_required
def get_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    return jsonify(payment.to_dict())


# ------------------------CREATE A payment--------------------
@payment_routes.route("/", methods=["POST"])
@payment_routes.route("", methods=["POST"])
@login_required
def create_payment():
    data = request.get_json()
    try:
        payment = Payment(
            order_id=data["order_id"],
            cashier_id=current_user.id,  # Use current_user.id as cashier_id
            amount=data["amount"],
            method=data["method"],
            status=data.get("status", "pending"),
            transaction_id=data.get("transaction_id"),
            tip_amount=data.get("tip_amount", 0.0),
            tax_amount=data.get("tax_amount", 0.0),
            discount=data.get("discount", 0.0)
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify(payment.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

# ---------------------------CHANGE OR UPDATE A payment------------
@payment_routes.route("/<int:payment_id>", methods=["PUT"])
@payment_routes.route("/<int:payment_id>/", methods=["PUT"])
@login_required
def update_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    data = request.get_json()
    try:
        for field in ['order_id', 'amount', 'method', 'status', 'transaction_id', 'tip_amount', 'tax_amount', 'discount']:
            if field in data:
                setattr(payment, field, data[field])
        db.session.commit()
        return jsonify(payment.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ------------------------DELETE A payment----------------------
@payment_routes.route("/<int:payment_id>", methods=["DELETE"])
@payment_routes.route("/<int:payment_id>/", methods=["DELETE"])
@login_required
def delete_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    try:
        db.session.delete(payment)
        db.session.commit()
        return jsonify({"message": "Payment deleted"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

def process_payment(payment_data):
    """Process payment through M-Pesa or credit card"""
    try:
        if payment_data["method"] == "mpesa":
            return process_mpesa_payment(payment_data)
        elif payment_data["method"] in ["credit_card", "debit_card"]:
            return process_card_payment(payment_data)
        elif payment_data["method"] == "cash":
            return True  # Cash payments always succeed
        else:
            return False
    except Exception:
        return False

def process_mpesa_payment(payment_data):
    """Simulate M-Pesa payment processing"""
    # In a real implementation, this would call the M-Pesa API
    print(f"Processing M-Pesa payment for {payment_data['amount']}")
    # time.sleep(1)  # Simulate network delay #remove the time library
    # Always return True for simulation
    return True

def process_card_payment(payment_data):
    """Simulate card payment processing"""
    # In a real implementation, this would call a payment gateway
    print(f"Processing card payment for {payment_data['amount']}")
    # time.sleep(1)  # Simulate network delay #remove the time library
    # Always return True for simulation
    return True