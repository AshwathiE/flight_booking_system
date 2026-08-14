from backend.database.connection import engine, Base
from backend.models.user import User
from backend.models.admin import Admin
from backend.models.flight import Flight

print("Creating database tables for User, Admin, Flight...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")