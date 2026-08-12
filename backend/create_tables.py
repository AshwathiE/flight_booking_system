from backend.database.connection import engine, Base

from backend.models.flight import Flight


Base.metadata.create_all(bind=engine)

print("Database tables created successfully")