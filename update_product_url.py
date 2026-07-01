import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

cur.execute("""
    UPDATE products 
    SET competitor_url = %s
    WHERE sku = %s
""",(
    "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    "WM-X1-001"
))

conn.commit()
print("Product URL updated successfully.")

cur.close()
conn.close()

