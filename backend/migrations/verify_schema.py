import psycopg2
import os
import re
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
m = re.match(r"postgresql(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+):?(\d+)?/(.+)", DATABASE_URL)
user, password, host, port, dbname = m.groups()
port = int(port) if port else 5432

conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_name='bookings'
    ORDER BY ordinal_position
""")
rows = cur.fetchall()
print(f"{'Column':<25} {'Type':<30} {'Nullable':<10} {'Default'}")
print("-" * 85)
for row in rows:
    print(f"{row[0]:<25} {row[1]:<30} {row[2]:<10} {row[3] or ''}")
conn.close()
