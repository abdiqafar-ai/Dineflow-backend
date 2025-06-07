from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from models import db, Payment, Order, OrderItem, MenuCategory, MenuItem  # Import Order and OrderItem
from flask_login import login_required, current_user
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy.orm import joinedload

menu_routes = Blueprint("menu_routes", __name__, url_prefix="/api/menu")


# Context manager for safe database operations
@contextmanager
def session_scope():
    session = db.session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()

# ========== MENU CATEGORY ENDPOINTS ==========

# ------------------------- Get list of categories ---------------------------
@menu_routes.route("/categories", methods=["GET"])
def get_categories():
    categories = MenuCategory.query.filter_by(parent_id=None).order_by(MenuCategory.display_order).all()
    return jsonify([cat.to_dict() for cat in categories])


# -------------------------------------- get a specific category -------------------
@menu_routes.route("/categories/<int:category_id>", methods=["GET"])
def get_category(category_id):
    category = MenuCategory.query.get_or_404(category_id)
    return jsonify(category.to_dict())


# ------------------------------------- create a caategory ------------------
@menu_routes.route("/categories", methods=["POST"])
@login_required
def create_category():
    data = request.get_json()
    try:
        with session_scope() as session:
            category = MenuCategory(
                name=data["name"],
                display_order=data.get("display_order", 0),
                parent_id=data.get("parent_id"),
                is_active=data.get("is_active", True)
            )
            session.add(category)
        return jsonify(category.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ----------------------- update or change the data of a certain category-----------------------------
@menu_routes.route("/categories/<int:category_id>", methods=["PUT"])
@login_required
def update_category(category_id):
    category = MenuCategory.query.get_or_404(category_id)
    data = request.get_json()
    try:
        if "name" in data:
            category.name = data["name"]
        if "display_order" in data:
            category.display_order = data["display_order"]
        if "parent_id" in data:
            category.parent_id = data["parent_id"]
        if "is_active" in data:
            category.is_active = data["is_active"]

        db.session.commit()
        return jsonify(category.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ----------------------DELETE A CATEGORY------------------------
@menu_routes.route("/categories/<int:category_id>", methods=["DELETE"])
@login_required
def delete_category(category_id):
    category = MenuCategory.query.get_or_404(category_id)
    try:
        with session_scope() as session:
            session.delete(category)
        return jsonify({"message": "Category deleted"})
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500


# ========== MENU ITEM ENDPOINTS ==========


# -----------------------GET LIST OF ITEMS IN A CATEGORY-------------
@menu_routes.route("/items", methods=["GET"])
def get_menu_items():
    category_id = request.args.get("category_id")
    query = MenuItem.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    items = query.order_by(MenuItem.name).all()
    return jsonify([item.to_dict() for item in items])


# -------------------------------GET A SPECIFIC ITEM-----------------
@menu_routes.route("/items/<int:item_id>", methods=["GET"])
def get_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    return jsonify(item.to_dict())


# -----------------CREATE AN ITEM---------------------
@menu_routes.route("/items", methods=["POST"])
@login_required
def create_menu_item():
    data = request.get_json()
    try:
        item = MenuItem(
            name             = data["name"],
            description      = data.get("description"),
            price            = data["price"],
            cost_price       = data.get("cost_price"),
            image_url        = data.get("image_url"),
            category_id      = data["category_id"],
            preparation_time = data.get("preparation_time", 15),
            calories         = data.get("calories"),
            is_available     = data.get("is_available", True),
            ingredients      = data.get("ingredients")
        )
        db.session.add(item)
        db.session.commit()

        # item is still bound to db.session, so to_dict() can lazily load if needed
        return jsonify(item.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# -----------------------------------CHANGE OR UPDATE AN ITEM--------
@menu_routes.route("/items/<int:item_id>", methods=["PUT"])
@login_required
def update_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    data = request.get_json()
    try:
        # Update allowed fields from the payload
        for field in ['name', 'description', 'price', 'cost_price', 'image_url', 
                      'category_id', 'preparation_time', 'calories', 
                      'is_available', 'ingredients']:
            if field in data:
                setattr(item, field, data[field])

        # Commit on the same session that loaded the item
        db.session.commit()

        return jsonify(item.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# --------------------------------- DELETE AN ITEM----------------------
@menu_routes.route("/items/<int:item_id>", methods=["DELETE"])
@login_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    try:
        with session_scope() as session:
            session.delete(item)
        return jsonify({"message": "Menu item deleted"})
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500


# ========== ORDER ENDPOINTS ==========

# --------------------- GET THE LIST OF ORDERS ----------------
@menu_routes.route("/orders", methods=["GET"])
@login_required
def get_orders():
    user_id = request.args.get("user_id")
    status = request.args.get("status")
    query = Order.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.created_at.desc()).all()
    return jsonify([order.to_dict() for order in orders])


# ----------------------------------GET A SPECFIC ORDERS----------
@menu_routes.route("/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    # Load via the same session that will serve the response
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # Optional: ensure users can only access their own orders (if needed)
    if order.user_id != current_user.id and current_user.role != "ADMIN":
        return jsonify({"error": "Forbidden"}), 403

    return jsonify(order.to_dict()), 200


# ------------------------CREATE AN ORDER--------------------
from routes.payment_routes import process_payment

@menu_routes.route("/orders", methods=["POST"])
@login_required
def create_order():
    data = request.get_json()
    try:
        with session_scope() as session:
            # Create order
            order = Order(
                user_id=data["user_id"],
                waiter_id=data.get("waiter_id"),
                table_id=data.get("table_id"),
                status=data.get("status", "pending"),
                notes=data.get("notes"),
                created_at=datetime.utcnow()
            )
            session.add(order)
            session.flush()  # Get order.id for order_items

            # Add order items
            items = data.get("order_items", [])
            order_items = []
            for item in items:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=item["menu_item_id"],
                    quantity=item.get("quantity", 1),
                    status=item.get("status", "pending"),
                    notes=item.get("notes"),  # Fixed: should be from item, not data
                    chef_id=item.get("chef_id")  # Fixed: should be from item
                )
                session.add(order_item)
                order_items.append(order_item)

            # Payment processing ONLY if payment data exists
            payment_data = data.get("payment")
            if payment_data:
                payment = Payment(
                    order_id=order.id,
                    cashier_id=current_user.id,
                    amount=payment_data["amount"],
                    method=payment_data["method"],
                    status='pending',
                    transaction_id=payment_data.get("transaction_id"),
                    tip_amount=payment_data.get("tip_amount", 0.0),
                    tax_amount=payment_data.get("tax_amount", 0.0),
                    discount=payment_data.get("discount", 0.0)
                )
                session.add(payment)
                session.flush()  # Ensure payment ID is available

                # Process payment
                payment_success = process_payment(payment_data)
                if payment_success:
                    payment.status = 'completed'
                    order.status = 'confirmed'
                else:
                    payment.status = 'failed'
                    order.status = 'payment_failed'

            # Build response while session is still open
            order_dict = order.to_dict()
            order_dict['order_items'] = [item.to_dict() for item in order_items]
            if payment_data:
                order_dict['payment'] = payment.to_dict()

        return jsonify(order_dict), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------CHANGE OR UPDATE AN ORDER------------
@menu_routes.route("/orders/<int:order_id>", methods=["PUT"])
@login_required
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()

    # Optional: Only allow the owner or an admin to update
    if order.user_id != current_user.id and current_user.role != "ADMIN":
        return jsonify({"error": "Forbidden"}), 403

    try:
        # Update allowed fields
        for field in ['waiter_id', 'table_id', 'status', 'notes']:
            if field in data:
                setattr(order, field, data[field])

        # Commit on the same session that loaded the order
        db.session.commit()

        # order is still bound to db.session, so to_dict() works
        return jsonify(order.to_dict()), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ------------------------DELETE AN ORDER----------------------
@menu_routes.route("/orders/<int:order_id>", methods=["DELETE"])
@login_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    try:
        with session_scope() as session:
            session.delete(order)
        return jsonify({"message": "Order deleted"})
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500


# ========== ORDER ITEM ENDPOINTS ==========

# -------------------- GET THE LIST OF ORDER-ITEMS ------------------
@menu_routes.route("/order-items", methods=["GET"])
@login_required
def get_order_items():
    order_id = request.args.get("order_id")
    menu_item_id = request.args.get("menu_item_id")
    status = request.args.get("status")
    query = OrderItem.query
    if order_id:
        query = query.filter_by(order_id=order_id)
    if menu_item_id:
        query = query.filter_by(menu_item_id=menu_item_id)
    if status:
        query = query.filter_by(status=status)
    order_items = query.all()
    return jsonify([item.to_dict() for item in order_items])


# -----------------------GET A SPECIFIC ORDER-LIST----------
@menu_routes.route("/order-items/<int:order_item_id>", methods=["GET"])
@login_required
def get_order_item(order_item_id):
    item = OrderItem.query.get_or_404(order_item_id)
    return jsonify(item.to_dict())


# --------------------------- CREATE AN ORDER-LIST ---------------
@menu_routes.route("/order-items", methods=["POST"])
@login_required
def create_order_item():
    data = request.get_json()
    try:
        # 1) Validate references
        order     = Order.query.get_or_404(data["order_id"])
        menu_item = MenuItem.query.get_or_404(data["menu_item_id"])

        # (Optional) check that the current user owns or may add to this order
        if order.user_id != current_user.id and current_user.role != "ADMIN":
            return jsonify({"error": "Forbidden"}), 403

        # 2) Create and add the OrderItem
        item = OrderItem(
            order_id     = order.id,
            menu_item_id = menu_item.id,
            quantity     = data.get("quantity", 1),
            status       = data.get("status", "pending"),
            notes        = data.get("notes"),
            chef_id      = data.get("chef_id")
        )
        db.session.add(item)
        db.session.commit()

        # 3) Return the bound item
        return jsonify(item.to_dict()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ------------------------CHANGE OR UPDATE AN ORDER LIST---------------------------
@menu_routes.route("/order-items/<int:order_item_id>", methods=["PUT"])
@login_required
def update_order_item(order_item_id):
    # Load on db.session
    item = OrderItem.query.get_or_404(order_item_id)
    data = request.get_json()

    # Optional: only owner or admin can update
    order = Order.query.get(item.order_id)
    if order.user_id != current_user.id and current_user.role != "ADMIN":
        return jsonify({"error": "Forbidden"}), 403

    try:
        # Apply allowed updates
        for field in ['quantity', 'status', 'notes', 'chef_id']:
            if field in data:
                setattr(item, field, data[field])

        # If they changed menu_item_id, validate it
        if 'menu_item_id' in data:
            MenuItem.query.get_or_404(data['menu_item_id'])
            item.menu_item_id = data['menu_item_id']

        db.session.commit()

        return jsonify(item.to_dict()), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ----------------------------DELETE AN ORDER LIST--------------------
@menu_routes.route("/order-items/<int:order_item_id>", methods=["DELETE"])
@login_required
def delete_order_item(order_item_id):
    item = OrderItem.query.get_or_404(order_item_id)
    try:
        with session_scope() as session:
            session.delete(item)
        return jsonify({"message": "Order item deleted"})
    except SQLAlchemyError as e:
        return jsonify({"error": str(e)}), 500