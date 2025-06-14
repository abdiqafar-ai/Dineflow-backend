from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from models import db
from models import Notification, User
from datetime import datetime, timedelta

notification_routes = Blueprint("notification_routes", __name__, url_prefix="/api/notifications")

# --------------------- GET USER NOTIFICATIONS --------------------
@notification_routes.route("/", methods=["GET"], strict_slashes=False)
@login_required
def get_notifications():
    try:
        # Get query parameters
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 20))
        
        # Base query with eager loading
        query = Notification.query.options(
            joinedload(Notification.sender),
            joinedload(Notification.recipient)
        ).filter_by(recipient_id=current_user.id)
        
        # Apply filters
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Order and limit
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        
        return jsonify([n.to_dict() for n in notifications])
    
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error: " + str(e)}), 500

# -------------------- GET UNREAD COUNT --------------------------
@notification_routes.route("/unread-count", methods=["GET"], strict_slashes=False)  
@login_required
def get_unread_count():
    try:
        count = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).count()
        
        return jsonify({"unread_count": count})
    
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error: " + str(e)}), 500

# -------------------- MARK AS READ -----------------------------
@notification_routes.route("/<int:notification_id>/read", methods=["PATCH"],strict_slashes=False)
@login_required
def mark_as_read(notification_id):
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_id=current_user.id
        ).first_or_404()
        
        if not notification.is_read:
            notification.is_read = True
            db.session.commit()
        
        return jsonify(notification.to_dict())
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 500

# -------------------- MARK ALL AS READ --------------------------
@notification_routes.route("/mark-all-read", methods=["PATCH"],strict_slashes=False)
@login_required
def mark_all_as_read():
    try:
        updated = Notification.query.filter_by(
            recipient_id=current_user.id,
            is_read=False
        ).update({"is_read": True})
        
        db.session.commit()
        return jsonify({"message": f"{updated} notifications marked as read"})
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 500

# -------------------- CREATE NOTIFICATION -----------------------
@notification_routes.route("/", methods=["POST"], strict_slashes=False)
@login_required
def create_notification():
    data = request.get_json()
    
    # Validate required fields
    if not all(field in data for field in ['recipient_id', 'title', 'message']):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        # Create notification
        notification = Notification(
            recipient_id=data['recipient_id'],
            sender_id=current_user.id,  # Ensure sender_id is set
            title=data['title'],
            message=data['message'],
            type=data.get('type', 'app'),
            priority=data.get('priority', 0),
            action_url=data.get('action_url'),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        # Send email notification if applicable
        recipient = User.query.get(data['recipient_id'])
        if recipient and recipient.email and recipient.email_notifications:
            notification.send_email(recipient.email)
        
        # Explicitly load sender relationship
        notification = Notification.query.options(db.joinedload(Notification.sender)).get(notification.id)
        
        return jsonify(notification.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# -------------------- DELETE NOTIFICATION -----------------------
@notification_routes.route("/<int:notification_id>", methods=["DELETE"],strict_slashes=False)
@login_required
def delete_notification(notification_id):
    try:
        notification = Notification.query.filter_by(
            id=notification_id,
            recipient_id=current_user.id
        ).first_or_404()
        
        db.session.delete(notification)
        db.session.commit()
        return jsonify({"message": "Notification deleted"})
    
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error: " + str(e)}), 500

    # -----------------------test authentication endpoint-----------------------
@notification_routes.route("/test-auth", methods=["GET"])
@login_required
def test_auth():
    return jsonify({
        "message": "Authenticated",
        "user": current_user.email,
        "user_id": current_user.id
    })