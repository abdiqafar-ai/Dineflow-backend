# backend/seed_admin.py
from dotenv import load_dotenv
load_dotenv() 

from app import create_app
from models.user import db, User, RoleEnum
from datetime import datetime

app = create_app()
print("Using DB URL:", app.config["SQLALCHEMY_DATABASE_URI"])

with app.app_context():
    # Ensure all migrations are applied; no need for create_all() here
    admin_email = "abdiqafar3468@gmail.com"
    admin = User.query.filter_by(email=admin_email).first()

    if not admin:
        print("Seeding new admin...")
        admin = User(
            full_name="Abdiqafar Ibrahim",
            email=admin_email,
            role=RoleEnum.ADMIN.value,
            status="active",
            created_at=datetime.utcnow()
        )
        admin.set_password("abdiqafar3468")
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user seeded.")
    else:
        print("🔄 Admin already exists. Resetting password/status...")
        admin.set_password("abdiqafar3468")
        admin.status = "active"
        db.session.commit()
        print("✅ Admin user reset.")
