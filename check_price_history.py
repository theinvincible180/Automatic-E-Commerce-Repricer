import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    SELECT 
        p.name,
        ph.old_price,
        ph.new_price,
        ph.reason,
        ph.changed_at
    FROM price_history ph
    JOIN products p ON ph.product_id = p.id
    ORDER BY ph.changed_at DESC
""")

rows = cur.fetchall()

if not rows:
    print("No price history yet.")
else:
    for row in rows:
        name, old, new, reason, changed_at = row
        print(f"Product  : {name}")
        print(f"Change   : £{old} → £{new}")
        print(f"Reason   : {reason}")
        print(f"When     : {changed_at}")
        print()

cur.close()
conn.close()