import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("SELECT id, name, sku, competitor_url, our_cost, min_margin_percent, max_price, current_price FROM products")
rows = cur.fetchall()

for row in rows:
    print(row)

cur.close()
conn.close()