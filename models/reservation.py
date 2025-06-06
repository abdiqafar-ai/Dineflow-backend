from datetime import datetime
from sqlalchemy.orm import validates
from . import db

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    table_id          = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    reservation_time  = db.Column(db.DateTime, nullable=False, index=True)
    duration          = db.Column(db.Integer, nullable=False, default=60)  # duration in minutes
    guests            = db.Column(db.Integer, nullable=False)
    status            = db.Column(db.String(20), default="pending")  # pending, confirmed, canceled, seated
    special_requests  = db.Column(db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship(
        "User",
        back_populates="reservations"
    )
    table = db.relationship(
        'Table',
        back_populates='reservations',
        lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user": self.user.to_dict() if self.user else None,
            "table": self.table.to_dict() if self.table else None,
            "reservation_time": self.reservation_time.isoformat(),
            "duration": self.duration,
            "guests": self.guests,
            "status": self.status,
            "special_requests": self.special_requests
        }

    @validates('guests')
    def validate_guests(self, key, guests: int) -> int:
        if self.table_id:
            from .table import Table
            table = Table.query.get(self.table_id)
            if table and guests > table.capacity:
                raise ValueError(f"Exceeds table capacity ({table.capacity})")
        return guests

    @staticmethod
    def is_table_available(table_id, reservation_time, duration=60, exclude_reservation_id=None):
        from datetime import timedelta
        # Calculate the end time of the requested reservation
        new_start = reservation_time
        new_end = new_start + timedelta(minutes=duration)
        query = Reservation.query.filter(Reservation.table_id == table_id)
        if exclude_reservation_id is not None:
            query = query.filter(Reservation.id != exclude_reservation_id)
        # Only consider reservations that overlap with the requested time
        reservations = query.filter(
            Reservation.status.in_(["pending", "confirmed"]),
            Reservation.reservation_time < new_end
        ).all()
        # Check for overlaps in Python
        for r in reservations:
            existing_end = r.reservation_time + timedelta(minutes=r.duration)
            if existing_end > new_start:
                return False
        return True