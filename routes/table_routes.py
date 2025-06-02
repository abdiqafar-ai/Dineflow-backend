from flask import Blueprint, request, jsonify
from models import db, Table, Reservation
from sqlalchemy.exc import IntegrityError
from utils.auth_decorators import admin_required
from flask_login import login_required, current_user
from datetime import datetime

# Blueprint
table_bp = Blueprint('table_bp', __name__, url_prefix='/api/table')


# Create a new table
@table_bp.route('/tables', methods=['POST'])
@admin_required
def create_table():
    data = request.get_json()
    try:
        table = Table(
            number=data['number'],
            capacity=data['capacity'],
            location=data.get('location'),
            status=data.get('status', 'available'),
            qr_code=data.get('qr_code'),
            description=data.get('description')
        )
        db.session.add(table)
        db.session.commit()
        return jsonify(table.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Table number already exists."}), 400


# Get all tables (Admins, Waiters, etc.)
@table_bp.route('/tables', methods=['GET'])
@login_required
def get_all_tables():
    tables = Table.query.all()
    return jsonify([t.to_dict() for t in tables]), 200


# Get single table by ID
@table_bp.route('/tables/<int:table_id>', methods=['GET'])
@login_required
def get_table(table_id):
    table = Table.query.get_or_404(table_id)
    return jsonify(table.to_dict()), 200


# Update a table
@table_bp.route('/tables/<int:table_id>', methods=['PUT', 'PATCH'])
@admin_required
def update_table(table_id):
    table = Table.query.get_or_404(table_id)
    data = request.get_json()

    table.number = data.get('number', table.number)
    table.capacity = data.get('capacity', table.capacity)
    table.location = data.get('location', table.location)
    table.status = data.get('status', table.status)
    table.qr_code = data.get('qr_code', table.qr_code)
    table.description = data.get('description', table.description)

    db.session.commit()
    return jsonify(table.to_dict()), 200


# Delete a table
@table_bp.route('/tables/<int:table_id>', methods=['DELETE'])
@admin_required
def delete_table(table_id):
    table = Table.query.get_or_404(table_id)
    db.session.delete(table)
    db.session.commit()
    return jsonify({"message": "Table deleted successfully"}), 200


# Change table status (e.g., to occupied, reserved, available)
@table_bp.route('/tables/<int:table_id>/status', methods=['PATCH'])
@admin_required
def update_table_status(table_id):
    table = Table.query.get_or_404(table_id)
    data = request.get_json()
    status = data.get('status')

    if status not in ['available', 'reserved', 'occupied']:
        return jsonify({"error": "Invalid status"}), 400

    table.status = status
    db.session.commit()
    return jsonify({"message": f"Table status updated to {status}"}), 200


# Get all available tables
@table_bp.route('/tables/available', methods=['GET'])
@login_required
def get_available_tables():
    tables = Table.query.filter_by(status='available').all()
    return jsonify([t.to_dict() for t in tables]), 200

# Count tables by status
@table_bp.route('/status', methods=['GET'])
@admin_required
def table_stats():
    total = Table.query.count()
    available = Table.query.filter_by(status='available').count()
    reserved = Table.query.filter_by(status='reserved').count()
    occupied = Table.query.filter_by(status='occupied').count()

    return jsonify({
        "total": total,
        "available": available,
        "reserved": reserved,
        "occupied": occupied
    }), 200


# Get reserved tables with user and reservation time
@table_bp.route('/reserved', methods=['GET'])
@admin_required
def get_reserved_tables():
    reservations = Reservation.query.filter_by(status='reserved').all()
    result = []
    for r in reservations:
        result.append({
            "table": r.table.to_dict(),
            "user": r.user.to_dict(),
            "reserved_at": r.reserved_at.isoformat()
        })
    return jsonify(result), 200


# Get occupied tables with user details
@table_bp.route('/occupied', methods=['GET'])
@admin_required
def get_occupied_tables():
    reservations = Reservation.query.filter_by(status='occupied').all()
    result = []
    for r in reservations:
        result.append({
            "table": r.table.to_dict(),
            "user": r.user.to_dict(),
            "occupied_at": r.occupied_at.isoformat() if r.occupied_at else None
        })
    return jsonify(result), 200


# Get current user's reserved tables
@table_bp.route('/my-reservations', methods=['GET'])
@login_required
def get_my_reserved_tables():
    user_reservations = current_user.reservations.filter_by(status='reserved').all()
    result = []
    for reservation in user_reservations:
        result.append({
            "table": reservation.table.to_dict(),
            "reservation_time": reservation.reservation_time.isoformat(),
            "status": reservation.status
        })
    return jsonify(result), 200



# Get current user's occupied tables
@table_bp.route('/my-occupied', methods=['GET'])
@login_required
def get_my_occupied_tables():
    user_occupied = current_user.reservations.filter_by(status='occupied').all()
    result = []
    for reservation in user_occupied:
        result.append({
            "table": reservation.table.to_dict(),
            "occupied_since": reservation.start_time.isoformat() if reservation.start_time else None,
            "status": reservation.status
        })
    return jsonify(result), 200

@table_bp.route('/my-tables', methods=['GET'])
@login_required
def get_my_tables():
    reservations = Reservation.query.filter_by(user_id=current_user.id).all()
    return jsonify([
        {
            "reservation_id": r.id,
            "table_id": r.table_id,
            "reservation_time": r.reservation_time.isoformat(),
            "duration": r.duration,
            "status": r.status
        } for r in reservations
    ]), 200

@table_bp.route('/my-tables/<int:reservation_id>', methods=['GET'])
@login_required
def get_my_single_table(reservation_id):
    reservation = Reservation.query.filter_by(id=reservation_id, user_id=current_user.id).first()
    if not reservation:
        return jsonify({"error": "Reservation not found"}), 404

    return jsonify({
        "reservation_id": reservation.id,
        "table_id": reservation.table_id,
        "reservation_time": reservation.reservation_time.isoformat(),
        "duration": reservation.duration,
        "status": reservation.status
    }), 200

