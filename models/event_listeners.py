from sqlalchemy import event
from datetime import timedelta
from . import db
from .order import Order
from .order_item import OrderItem
from .reservation import Reservation

# OrderItem after_insert event
@event.listens_for(OrderItem, 'after_insert')
def update_order_estimation(mapper, connection, target):
    order = Order.query.get(target.order_id)
    if order:
        order.update_estimation()
        db.session.add(order)

# Reservation before_insert event
@event.listens_for(Reservation, 'before_insert')
def validate_reservation_time(mapper, connection, target):
    """Prevent double-booking of tables during the reservation time slot"""

    if not target.reservation_time or not target.duration:
        raise ValueError("Reservation must include both time and duration.")

    new_start = target.reservation_time
    new_end = new_start + timedelta(minutes=target.duration)

    # Get all possible conflicting reservations
    reservations = Reservation.query.filter(
        Reservation.table_id == target.table_id,
        Reservation.status.in_(["confirmed", "pending"]),
        Reservation.reservation_time < new_end
    ).all()

    for reservation in reservations:
        existing_end = reservation.reservation_time + timedelta(minutes=reservation.duration)
        if existing_end > new_start:
            raise ValueError("Table already booked for this time slot.")