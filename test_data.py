import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    INSERT INTO products(name, sku, competitor_url, our_cost, min_margin_percent, max_price, current_price)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""",(
    "Wireless Mouse X1",
    "WM-X1-001",
    "https://example.com/product/wireless-mouse-x1",
    15.00,    
    20.00,    
    45.00,    
    29.99
))

conn.commit()
print("Product inserted successfully.")

conn.close()
cur.close()