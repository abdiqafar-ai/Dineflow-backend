from . import db

class Table(db.Model):
    __tablename__ = 'tables'

    id          = db.Column(db.Integer, primary_key=True)
    number      = db.Column(db.Integer, unique=True, nullable=False, index=True)
    capacity    = db.Column(db.Integer, nullable=False)
    location    = db.Column(db.String(100), nullable=True)
    status      = db.Column(db.String(20), default="available", server_default="available")
    qr_code     = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), nullable=True)

    # One Table → Many Reservations
    reservations = db.relationship(
        'Reservation',
        back_populates='table',
        cascade='all, delete-orphan',
        lazy='dynamic',
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "number": self.number,
            "capacity": self.capacity,
            "location": self.location,
            "status": self.status,
            "qr_code": self.qr_code,
            "description": self.description
        }
