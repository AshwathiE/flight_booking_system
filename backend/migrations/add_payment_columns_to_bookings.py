"""
Migration: Add payment columns to bookings table
================================================
Adds missing columns introduced by the payment-first booking flow:
    - payment_status
    - payment_id
    - paid_at
    - ticket_status
    - updated_at

Run once against your PostgreSQL database:
    python -m backend.migrations.add_payment_columns_to_bookings
"""

import os
import sys

# Allow running from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in .env")

# Parse the DATABASE_URL into psycopg2 kwargs
# Expected format: postgresql://user:password@host:port/dbname
import re
match = re.match(
    r"postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)",
    DATABASE_URL,
)
if not match:
    raise RuntimeError(f"Cannot parse DATABASE_URL: {DATABASE_URL}")

user, password, host, port, dbname = match.groups()
port = int(port) if port else 5432

MIGRATIONS = [
    # payment_status column
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='bookings' AND column_name='payment_status'
        ) THEN
            ALTER TABLE bookings
            ADD COLUMN payment_status VARCHAR(30) NOT NULL DEFAULT 'PENDING';
            RAISE NOTICE 'Added payment_status column';
        ELSE
            RAISE NOTICE 'payment_status already exists, skipped';
        END IF;
    END $$;
    """,

    # payment_id column
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='bookings' AND column_name='payment_id'
        ) THEN
            ALTER TABLE bookings
            ADD COLUMN payment_id VARCHAR(100) UNIQUE DEFAULT NULL;
            RAISE NOTICE 'Added payment_id column';
        ELSE
            RAISE NOTICE 'payment_id already exists, skipped';
        END IF;
    END $$;
    """,

    # paid_at column
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='bookings' AND column_name='paid_at'
        ) THEN
            ALTER TABLE bookings
            ADD COLUMN paid_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;
            RAISE NOTICE 'Added paid_at column';
        ELSE
            RAISE NOTICE 'paid_at already exists, skipped';
        END IF;
    END $$;
    """,

    # ticket_status column
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='bookings' AND column_name='ticket_status'
        ) THEN
            ALTER TABLE bookings
            ADD COLUMN ticket_status VARCHAR(30) NOT NULL DEFAULT 'NOT_AVAILABLE';
            RAISE NOTICE 'Added ticket_status column';
        ELSE
            RAISE NOTICE 'ticket_status already exists, skipped';
        END IF;
    END $$;
    """,

    # updated_at column
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='bookings' AND column_name='updated_at'
        ) THEN
            ALTER TABLE bookings
            ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
            RAISE NOTICE 'Added updated_at column';
        ELSE
            RAISE NOTICE 'updated_at already exists, skipped';
        END IF;
    END $$;
    """,

    # Backfill: existing rows that were CONFIRMED should stay CONFIRMED
    # Existing rows without payment_status get default PENDING (already set above)
    # Rows with status=CONFIRMED should get payment_status=SUCCESS
    """
    UPDATE bookings
    SET payment_status = 'SUCCESS',
        ticket_status  = 'AVAILABLE'
    WHERE status = 'CONFIRMED'
      AND payment_status = 'PENDING';
    """,
]


def run_migrations():
    print(f"Connecting to database: {host}:{port}/{dbname} as {user}")
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    for i, sql in enumerate(MIGRATIONS, 1):
        print(f"\n--- Running migration step {i}/{len(MIGRATIONS)} ---")
        cursor.execute(sql)
        print(f"    Step {i} complete.")

    cursor.close()
    conn.close()
    print("\n✅ All migrations completed successfully!")


if __name__ == "__main__":
    run_migrations()
