from backend.database.connection import engine
from sqlalchemy import text

def run_migration():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
            print("Added 'role' column.")
        except Exception as e:
            print("Could not add 'role' column, it may already exist:", e)

        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN status VARCHAR(50) DEFAULT 'active'"))
            print("Added 'status' column.")
        except Exception as e:
            print("Could not add 'status' column, it may already exist:", e)

if __name__ == "__main__":
    run_migration()
