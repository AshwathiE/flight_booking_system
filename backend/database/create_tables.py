from backend.database.connection import engine, Base

# Import models so SQLAlchemy knows about them
from backend.models.flight import Flight


print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")