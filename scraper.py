import os
import re
from dotenv import load_dotenv
import psycopg2
from playwright.sync_api import sync_playwright

load_dotenv()


def get_urls_to_scrape():
    """Fetch all active competitor URLs grouped with their product info."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        SELECT cu.product_id, p.name, cu.competitor_name, cu.url
        FROM competitor_urls cu
        JOIN products p ON cu.product_id = p.id
        WHERE cu.is_active = TRUE
    """)
    urls = cur.fetchall()
    cur.close()
    conn.close()
    return urls


def scrape_price(page, url):
    """Navigate to a URL and extract the price."""
    try:
        page.goto(url, timeout=30000)
        page.wait_for_selector(".price_color", timeout=10000)
        price_text = page.locator(".price_color").first.inner_text()
        print(f"    Raw price text: {price_text}")
        price_clean = re.sub(r"[^\d.]", "", price_text)
        return float(price_clean)
    except Exception as e:
        print(f"    Error scraping {url}: {e}")
        return None


def save_competitor_price(product_id, competitor_name, price):
    """Write a scraped price into the competitor_prices table."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO competitor_prices (product_id, competitor_name, scraped_price)
        VALUES (%s, %s, %s)
    """, (product_id, competitor_name, price))
    conn.commit()
    cur.close()
    conn.close()


def run_scraper():
    urls = get_urls_to_scrape()
    print(f"Found {len(urls)} competitor URLs to scrape.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        current_product = None
        for product_id, product_name, competitor_name, url in urls:

            # Print product name only when it changes (groups output nicely)
            if product_name != current_product:
                print(f"Product: {product_name}")
                current_product = product_name

            print(f"  Competitor: {competitor_name}")
            print(f"  URL: {url}")

            price = scrape_price(page, url)

            if price is not None:
                print(f"  Extracted price: £{price}")
                save_competitor_price(product_id, competitor_name, price)
                print(f"  Saved to DB.")
            else:
                print(f"  Could not extract price, skipping.")
            print()

        browser.close()

    print("Scraping complete.")


if __name__ == "__main__":
    run_scraper()