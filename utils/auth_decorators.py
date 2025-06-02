# utils/auth_decorators.py

from flask import jsonify
from flask_login import current_user
from functools import wraps
from models.user import RoleEnum 

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role != RoleEnum.ADMIN.value:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function
