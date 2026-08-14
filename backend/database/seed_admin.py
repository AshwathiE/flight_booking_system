import os

from dotenv import load_dotenv

from backend.database.connection import SessionLocal
from backend.models.admin import Admin
from backend.services.auth_service import hash_password

load_dotenv()


def create_initial_admin():

    db = SessionLocal()

    try:
        email = os.getenv("INITIAL_ADMIN_EMAIL")

        existing_admin = (
            db.query(Admin)
            .filter(Admin.email == email)
            .first()
        )

        if existing_admin:
            print("Admin already exists.")
            return

        admin = Admin(
            name=os.getenv("INITIAL_ADMIN_NAME"),
            email=email,
            password_hash=hash_password(
                os.getenv("INITIAL_ADMIN_PASSWORD")
            ),
            role="super_admin",
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Initial admin created successfully.")
        print(f"Email: {admin.email}")

    finally:
        db.close()


if __name__ == "__main__":
    create_initial_admin()