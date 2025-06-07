from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from models import db
from models.reservation import Reservation
from utils.auth_decorators import admin_required
from flask_login import login_required

reservation_routes = Blueprint("reservation_routes", __name__, url_prefix="/api/reservations")

@reservation_routes.route("", methods=["POST"])
@login_required
def create_reservation():
    data = request.get_json()
    try:
        if "reservation_time" not in data:
            return jsonify({"error": "Reservation must include a reservation_time."}), 400

        reservation_time = datetime.fromisoformat(data["reservation_time"])
        duration = int(data.get("duration", 60))

        if not Reservation.is_table_available(
            table_id=data["table_id"],
            reservation_time=reservation_time,
            duration=duration
        ):
            return jsonify({"error": "Table not available at that time"}), 400

        reservation = Reservation(
            user_id=data["user_id"],
            table_id=data["table_id"],
            reservation_time=reservation_time,
            duration=duration,
            guests=data["guests"],
            special_requests=data.get("special_requests")
        )

        db.session.add(reservation)
        db.session.commit()
        return jsonify(reservation.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@reservation_routes.route("", methods=["GET"])
@login_required
def get_reservations():
    status = request.args.get("status")
    user_id = request.args.get("user_id")
    date_str = request.args.get("date")

    query = Reservation.query
    if status:
        query = query.filter_by(status=status)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if date_str:
        try:
            date = datetime.fromisoformat(date_str).date()
            query = query.filter(db.func.date(Reservation.reservation_time) == date)
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

    reservations = query.order_by(Reservation.reservation_time).all()
    return jsonify([r.to_dict() for r in reservations])

@reservation_routes.route("/<int:reservation_id>", methods=["GET"])
@login_required
def get_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    return jsonify(reservation.to_dict())

@reservation_routes.route("/<int:reservation_id>", methods=["PUT"])
@login_required
def update_reservation(reservation_id):
    data = request.get_json()
    reservation = Reservation.query.get_or_404(reservation_id)

    try:
        if "reservation_time" in data:
            reservation.reservation_time = datetime.fromisoformat(data["reservation_time"])
        if "duration" in data:
            reservation.duration = int(data["duration"])

        if not Reservation.is_table_available(
            table_id=reservation.table_id,
            reservation_time=reservation.reservation_time,
            duration=reservation.duration,
            exclude_reservation_id=reservation.id
        ):
            return jsonify({"error": "Table not available at the new time"}), 400

        if "guests" in data:
            reservation.guests = data["guests"]
        if "status" in data:
            reservation.status = data["status"]
        if "special_requests" in data:
            reservation.special_requests = data["special_requests"]

        db.session.commit()
        return jsonify(reservation.to_dict())

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@reservation_routes.route("/<int:reservation_id>", methods=["DELETE"])
@admin_required
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    try:
        db.session.delete(reservation)
        db.session.commit()
        return jsonify({"message": "Reservation deleted"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@reservation_routes.route("/<int:reservation_id>/status", methods=["PATCH"])
@admin_required
def update_reservation_status(reservation_id):
    data = request.get_json()
    reservation = Reservation.query.get_or_404(reservation_id)
    status = data.get("status")

    if not status:
        return jsonify({"error": "Missing status"}), 400

    reservation.status = status
    db.session.commit()
    return jsonify(reservation.to_dict())

@reservation_routes.route("/check-availability", methods=["POST"])
@login_required
def check_availability():
    data = request.get_json()
    try:
        if "reservation_time" not in data:
            return jsonify({"error": "Missing reservation_time"}), 400

        table_id = data["table_id"]
        reservation_time = datetime.fromisoformat(data["reservation_time"])
        duration = int(data.get("duration", 60))
        available = Reservation.is_table_available(table_id, reservation_time, duration)
        return jsonify({"available": available})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@reservation_routes.route("/upcoming", methods=["GET"])
@login_required
def upcoming_reservations():
    user_id = request.args.get("user_id")
    from_time = datetime.utcnow()

    query = Reservation.query.filter(Reservation.reservation_time >= from_time)
    if user_id:
        query = query.filter_by(user_id=user_id)

    reservations = query.order_by(Reservation.reservation_time).all()
    return jsonify([r.to_dict() for r in reservations])