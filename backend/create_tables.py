from backend.database.connection import engine, Base
from backend.models.user import User
from backend.models.admin import Admin
from backend.models.flight import Flight

Base.metadata.create_all(bind=engine)
print("Database tables created successfully")