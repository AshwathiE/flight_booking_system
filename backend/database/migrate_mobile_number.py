import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def run_migration():
    print(f"Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mobile_number VARCHAR(50) DEFAULT ''"))
            print("Successfully added 'mobile_number' column to users table.")
        except Exception as e:
            print("Error adding mobile_number column (it may already exist):", e)

if __name__ == "__main__":
    run_migration()
