from sqlalchemy import event
from datetime import timedelta
from . import db
from .menu import Order, OrderItem  # Combined models file
from .reservation import Reservation

# OrderItem after_insert event
@event.listens_for(OrderItem, 'after_insert')
def flag_order_for_estimation_update(mapper, connection, target):
    """Flag the order for estimation update."""
    target.order_requires_estimation_update = True

@event.listens_for(db.session, 'after_flush')
def update_estimation_after_flush(session, flush_context):
    """Update estimation for orders that require it after the flush."""
    for obj in session.dirty:
        if isinstance(obj, OrderItem) and hasattr(obj, 'order_requires_estimation_update') and obj.order_requires_estimation_update:
            order = db.session.get(Order, obj.order_id)
            if order:
                order.update_estimation()
                del obj.order_requires_estimation_update  # Clean up flag

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