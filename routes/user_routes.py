from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from models.user import db,User
from sqlalchemy import func
from utils.auth_decorators import admin_required

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/user')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@user_bp.route('/avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['avatar']
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{current_user.id}_{file.filename}")
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        current_user.avatar_url = f"/static/avatars/{filename}"
        db.session.commit()
        return jsonify({"avatar_url": current_user.avatar_url}), 200

    return jsonify({"error": "Invalid file type"}), 400

@user_bp.route('/me', methods=['GET'])
@login_required
def get_profile():
    return jsonify(current_user.to_dict())


@user_bp.route('/', methods=['GET'])
@login_required
@admin_required
def get_all_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user_by_id(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200



@user_bp.route('/count', methods=['GET'])
@login_required
def count_users():
    total_users = User.query.count()
    return jsonify({"total_users": total_users})



@user_bp.route('/count/by-role', methods=['GET'])
@login_required
def count_users_by_role():
    role_counts = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    return jsonify({role: count for role, count in role_counts})

from datetime import datetime, timedelta

@user_bp.route('/status/<int:user_id>', methods=['PATCH'])
@login_required
@admin_required
def change_user_status(user_id):
    data = request.get_json()
    new_status = data.get("status")  # active, suspended, banned
    suspend_days = data.get("days")  # Optional, for suspension

    if new_status not in ["active", "suspended", "banned"]:
        return jsonify({"error": "Invalid status"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if new_status == "suspended":
        if not suspend_days:
            return jsonify({"error": "Suspension duration ('days') required"}), 400
        user.suspension_ends_at = datetime.utcnow() + timedelta(days=int(suspend_days))
    else:
        user.suspension_ends_at = None

    user.status = new_status
    db.session.commit()
    return jsonify({"message": f"User status changed to {new_status}"}), 200

@user_bp.route('/update', methods=['PATCH'])
@login_required
def update_user():
    data = request.get_json()
    allowed_fields = ['email', 'gender', 'avatar_url']
    
    for field in allowed_fields:
        if field in data:
            setattr(current_user, field, data[field])

    db.session.commit()
    return jsonify({"message": "Account updated successfully", "user": current_user.to_dict()}), 200

@user_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({"message": "Account deleted successfully"}), 200

@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user_by_admin(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200

@user_bp.route('/role/<int:user_id>', methods=['PATCH'])
@login_required
@admin_required
def change_user_role(user_id):
    data = request.get_json()
    new_role = data.get("role")
    if new_role not in ["Admin", "Chef", "Waiter", "Customer","Cashier"]:
        return jsonify({"error": "Invalid role"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role = new_role
    db.session.commit()
    return jsonify({"message": f"User role changed to {new_role}"}), 200

@user_bp.route('/count/by-status', methods=['GET'])
@login_required
@admin_required
def count_users_by_status():
    status_counts = (
        db.session
          .query(User.status, func.count(User.id))
          .filter(User.status.in_(["active", "suspended", "banned"]))
          .group_by(User.status)
          .all()
    )

    result = { status: count for status, count in status_counts }
    # Ensure keys for all three statuses—even if count is zero
    for s in ["active", "suspended", "banned"]:
        result.setdefault(s, 0)

    return jsonify(result), 200


@user_bp.route('/list/active', methods=['GET'])
@login_required
@admin_required
def list_active_users():
    users = User.query.filter_by(status="active").all()
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.route('/list/suspended', methods=['GET'])
@login_required
@admin_required
def list_suspended_users():
    users = User.query.filter_by(status="suspended").all()
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.route('/list/banned', methods=['GET'])
@login_required
@admin_required
def list_banned_users():
    users = User.query.filter_by(status="banned").all()
    return jsonify([u.to_dict() for u in users]), 200

