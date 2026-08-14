from backend.database.connection import Base, engine, SessionLocal
from backend.models.admin import Admin
from backend.services.auth_service import hash_password


def create_admin():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        existing_admin = (
            db.query(Admin)
            .filter(Admin.email == "admin@flight.com")
            .first()
        )

        if existing_admin:
            print("Admin already exists (admin@flight.com). Updating password hash...")
            existing_admin.password_hash = hash_password("admin123")
            db.commit()
            print("Admin password updated successfully.")
            return

        admin = Admin(
            name="System Admin",
            email="admin@flight.com",
            password_hash=hash_password("admin123"),
            role="admin",
            status="active"
        )

        db.add(admin)
        db.commit()
        print("Admin created successfully (admin@flight.com / admin123).")

    except Exception as e:
        db.rollback()
        print(f"Error creating admin: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()