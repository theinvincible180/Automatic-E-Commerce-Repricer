import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    SELECT p.name, cp.competitor_name, cp.scraped_price, cp.scraped_at
    FROM competitor_prices cp
    JOIN products p ON cp.product_id = p.id
    ORDER BY p.name, cp.competitor_name, cp.scraped_at DESC
""")

rows = cur.fetchall()
for row in rows:
    print(row)

cur.close()
conn.close()