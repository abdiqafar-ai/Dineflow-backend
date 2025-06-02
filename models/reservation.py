from datetime import timedelta, datetime
from sqlalchemy.orm import validates

from . import db
# do not import Table or User at module scope to avoid circularity
# from .table import Table
# from .user import User

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    table_id          = db.Column(db.Integer, db.ForeignKey('tables.id'), nullable=False)
    reservation_time  = db.Column(db.DateTime, nullable=False, index=True)
    duration          = db.Column(db.Integer, nullable=False, default=60)
    guests            = db.Column(db.Integer, nullable=False)
    status            = db.Column(db.String(20), default="pending")  # pending, confirmed, canceled, seated
    special_requests  = db.Column(db.Text, nullable=True)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at        = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (string names break circular imports)
    user = db.relationship(
        "User",  
        back_populates="reservations"
        )
    table = db.relationship(
        'Table',
        back_populates='reservations',
        lazy=True
    )

    def end_time(self):
        if self.duration is None:
            raise ValueError("Reservation duration must be set before computing end time.")
        return self.reservation_time + timedelta(minutes=self.duration)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user": self.user.to_dict() if self.user else None,
            "table": self.table.to_dict() if self.table else None,
            "reservation_time": self.reservation_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "guests": self.guests,
            "status": self.status,
            "special_requests": self.special_requests
        }

    @validates('guests')
    def validate_guests(self, key, guests: int) -> int:
        """Ensure guests don’t exceed table capacity."""
        if self.table_id:
            # Import Table here at runtime (not at module load time)
            from .table import Table
            table = Table.query.get(self.table_id)
            if table and guests > table.capacity:
                raise ValueError(f"Exceeds table capacity ({table.capacity})")
        return guests
