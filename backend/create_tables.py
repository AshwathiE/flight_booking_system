from backend.database.connection import engine, Base
from backend.models.user import User
from backend.models.admin import Admin
from backend.models.flight import Flight
from backend.models.booking import Booking
from backend.models.payment import Payment
Base.metadata.create_all(bind=engine)
print("Database tables created successfully")