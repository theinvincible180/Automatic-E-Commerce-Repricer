import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cur = conn.cursor()

# First get the product id of our test product
cur.execute("SELECT id FROM products WHERE sku = %s", ("WM-X1-001",))
product = cur.fetchone()

if product:
    product_id = product[0]

    # Insert multiple competitor URLs for the same product
    competitors = [
        (product_id, "books_to_scrape_1", "http://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"),
        (product_id, "books_to_scrape_2", "http://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"),
        (product_id, "books_to_scrape_3", "http://books.toscrape.com/catalogue/soumission_998/index.html"),
    ]

    cur.executemany("""
        INSERT INTO competitor_urls (product_id, competitor_name, url)
        VALUES (%s, %s, %s)
    """, competitors)

    conn.commit()
    print(f"Inserted {len(competitors)} competitor URLs for product_id {product_id}.")
else:
    print("Product not found.")

cur.close()
conn.close()