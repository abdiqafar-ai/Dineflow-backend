from flask import Blueprint, request, jsonify, redirect, url_for
from werkzeug.security import generate_password_hash
from models.user import db, User, RoleEnum
from flask_login import login_user, logout_user, login_required
from utils.google_oauth import oauth
from datetime import datetime
import secrets
from flask_mail import Message

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    full_name = data.get('full_name')
    email = data.get('email')
    password = data.get('password')

    if not full_name or not email or not password:
        return jsonify({"error": "Full name, email, and password are required"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "User already exists"}), 400

    new_user = User(
        full_name=full_name,
        email=email,
        password_hash=generate_password_hash(password),
        role=RoleEnum.CUSTOMER
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Registration successful"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 415

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401

    if not user.password_hash:
        # No password set (likely a Google-created account)
        return jsonify({"error": "User must sign in via Google"}), 401

    if not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    if user.status == "banned":
        return jsonify({"error": "Account is banned"}), 403

    if user.status == "suspended":
        if user.suspension_ends_at and user.suspension_ends_at > datetime.utcnow():
            return jsonify({"error": f"Account is suspended until {user.suspension_ends_at}"}), 403
        else:
            # Suspension expired, optionally auto-activate user here
            user.status = "active"
            db.session.commit()

    login_user(user)
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "avatar_url": user.avatar_url
        }
    }), 200

@auth_bp.route('/google/login')
def google_login():
    redirect_uri = url_for('auth_bp.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@auth_bp.route('/google/callback')
def google_callback():
    # 1) Exchange code for tokens
    token = oauth.google.authorize_access_token()

    # 2) Fetch user info via the built-in helper
    user_info = oauth.google.userinfo()

    # 3) Find or create user in your DB
    user = User.query.filter_by(email=user_info['email']).first()
    if not user:
        user = User(
            full_name=user_info.get('name'),
            email=user_info['email'],
            role=RoleEnum.CUSTOMER,
            is_google_account=True,
            avatar_url=user_info.get("picture")
        )
        db.session.add(user)
        db.session.commit()

    # 4) Log in and redirect
    login_user(user)
    return redirect("http://localhost:3000/dashboard")

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "No user with that email"}), 404

    # Generate a reset token (you could also store expiration time)
    token = secrets.token_urlsafe(32)
    user.reset_token = token  # <-- Ensure this field exists in your User model
    db.session.commit()

    # You could send this via email in production
    reset_link = f"http://localhost:3000/reset-password/{token}"

    # Optional: Send email if using Flask-Mail
    # msg = Message("Password Reset", recipients=[email])
    # msg.body = f"Click this link to reset your password: {reset_link}"
    # mail.send(msg)

    return jsonify({"message": "Password reset link sent", "reset_link": reset_link}), 200

# ------------------  Reset Password ------------------

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({"error": "Token and new password are required"}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({"error": "Invalid or expired token"}), 400

    user.password_hash = generate_password_hash(new_password)
    user.reset_token = None  # Invalidate token after use
    db.session.commit()

    return jsonify({"message": "Password has been reset successfully"}), 200

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out"}), 200
