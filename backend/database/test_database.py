from backend.database.connection import engine

try:
    with engine.connect() as connection:
        print("PostgreSQL connected successfully!")

except Exception as e:
    print("Database connection failed:")
    print(e)