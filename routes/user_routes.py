from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from models.user import db,User, RoleEnum
from sqlalchemy import func
from utils.auth_decorators import admin_required

user_bp = Blueprint('user_bp', __name__, url_prefix='/api/user')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# upload avatar for the current user
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

# the current user's profile
@user_bp.route('/me', methods=['GET'])
@login_required
def get_profile():
    return jsonify(current_user.to_dict())

# get list of all users
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


# count total users
@user_bp.route('/count', methods=['GET'])
@login_required
def count_users():
    total_users = User.query.count()
    return jsonify({"total_users": total_users})


# count users by role
@user_bp.route('/count/by-role', methods=['GET'])
@login_required
def count_users_by_role():
    role_counts = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    return jsonify({role: count for role, count in role_counts})

from datetime import datetime, timedelta

# suspend or ban user by admin
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

# update current user's account information
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

# delete current user's account
@user_bp.route('/delete', methods=['DELETE'])
@login_required
def delete_account():
    db.session.delete(current_user)
    db.session.commit()
    return jsonify({"message": "Account deleted successfully"}), 200

# delete user by admin
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

# promote user by admin
@user_bp.route('/role/<int:user_id>', methods=['PATCH'])
@login_required
@admin_required
def change_user_role(user_id):
    data = request.get_json()
    new_role = data.get("role", "").upper()  # Convert to uppercase

    valid_roles = [role.value for role in RoleEnum]  # Use enum values for validation

    if new_role not in valid_roles:
        return jsonify({"error": "Invalid role"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user.role = new_role
    db.session.commit()
    return jsonify({"message": f"User role changed to {new_role}"}), 200


# count users by status
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

# List users by status
@user_bp.route('/list/active', methods=['GET'])
@login_required
@admin_required
def list_active_users():
    users = User.query.filter_by(status="active").all()
    return jsonify([u.to_dict() for u in users]), 200

# List users by status
@user_bp.route('/list/suspended', methods=['GET'])
@login_required
@admin_required
def list_suspended_users():
    users = User.query.filter_by(status="suspended").all()
    return jsonify([u.to_dict() for u in users]), 200

# List users by status
@user_bp.route('/list/banned', methods=['GET'])
@login_required
@admin_required
def list_banned_users():
    users = User.query.filter_by(status="banned").all()
    return jsonify([u.to_dict() for u in users]), 200

# demote user to higher role
role_hierarchy = ['CUSTOMER', 'WAITER', 'CHEF','CASHIER', 'ADMIN']

@user_bp.route('/<int:user_id>/demote', methods=['PUT'])
@login_required
@admin_required
def demote_user(user_id):
    user = User.query.get_or_404(user_id)

    try:
        current_index = role_hierarchy.index(user.role.upper())
    except ValueError:
        return jsonify({"error": f"Invalid user role: {user.role}"}), 400

    if current_index == 0:
        return jsonify({"error": "User is already at the lowest role (customer)."}), 400

    new_role = role_hierarchy[current_index - 1]
    user.role = new_role
    db.session.commit()

    return jsonify({"message": f"User demoted to {new_role}"}), 200

@user_bp.route('/<int:user_id>/promote', methods=['PUT'])
@login_required
@admin_required
def promote_user(user_id):
    user = User.query.get_or_404(user_id)

    # Normalize the role before comparison
    current_role = user.role.strip().upper()
    role_hierarchy = ['CUSTOMER', 'WAITER', 'CHEF', 'ADMIN']

    try:
        current_index = role_hierarchy.index(current_role)
    except ValueError:
        return jsonify({"error": f"Invalid user role: {user.role}"}), 400

    if current_index == len(role_hierarchy) - 1:
        return jsonify({"error": "User is already at the highest role (admin)."}), 400

    new_role = role_hierarchy[current_index + 1]
    user.role = new_role
    db.session.commit()

    return jsonify({"message": f"User promoted to {new_role}"}), 200

# unban a user by admin
@user_bp.route('/<int:user_id>/unban', methods=['PUT'])
@login_required
@admin_required
def unban_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.status != 'banned':
        return jsonify({"error": "User is not banned."}), 400

    user.status = 'active'
    db.session.commit()
    return jsonify({"message": "User has been unbanned and is now active."}), 200

# unsuspend a user by admin
@user_bp.route('/<int:user_id>/unsuspend', methods=['PUT'])
@login_required
@admin_required
def unsuspend_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.status != 'suspended':
        return jsonify({"error": "User is not suspended."}), 400

    user.status = 'active'
    user.suspension_ends_at = None
    db.session.commit()
    return jsonify({"message": "User suspension lifted, status set to active."}), 200

@user_bp.route('/welcome', methods=['GET'])
@login_required
def welcome_user():
    user = current_user

    first_time = user.last_login is None
    full_name = user.full_name

    message = (
        f"Welcome, {full_name}!" if first_time
        else f"Welcome back, {full_name}!"
    )

    # Update last_login to now if it's the first time
    user.last_login = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": message}), 200