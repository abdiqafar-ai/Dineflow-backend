from sqlalchemy import event
from . import db
from .order import Order
from .order_item import OrderItem
from .reservation import Reservation

# OrderItem after_insert event
@event.listens_for(OrderItem, 'after_insert')
def update_order_estimation(mapper, connection, target):
    """Update order ETA when new items are added"""
    order = Order.query.get(target.order_id)
    if order:
        order.update_estimation()
        db.session.add(order)

# Reservation before_insert event
from datetime import timedelta
from sqlalchemy import and_

@event.listens_for(Reservation, 'before_insert')
def validate_reservation_time(mapper, connection, target):
    """Prevent double-booking of tables during the reservation time slot"""

    if not target.reservation_time or not target.duration:
        raise ValueError("Reservation must include both time and duration.")

    # Calculate end time for the new reservation
    new_start = target.reservation_time
    new_end = new_start + timedelta(minutes=target.duration)

    # Check for overlapping reservations on the same table
    conflicting = Reservation.query.filter(
        Reservation.table_id == target.table_id,
        Reservation.status.in_(["confirmed", "pending"]),
        Reservation.reservation_time < new_end,
        (Reservation.reservation_time + timedelta(minutes=Reservation.duration)) > new_start
    ).first()

    if conflicting:
        raise ValueError("Table already booked for this time slot.")
