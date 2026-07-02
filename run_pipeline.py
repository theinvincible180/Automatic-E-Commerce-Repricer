import os
from dotenv import load_dotenv
import psycopg2
from scraper import run_scraper
from margin_agent import (
    get_product_with_latest_competitor_prices,
    run_margin_agent
)
from execution_agent import run_execution_agent

load_dotenv()


def get_all_product_ids():
    """Fetch all product IDs from the database."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    cur.execute("SELECT id FROM products")
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return ids


def run_full_pipeline():
    """
    The complete agentic loop:
    1. Monitoring Agent  — scrape competitor prices
    2. Margin Agent      — calculate optimal price
    3. Execution Agent   — update DB if needed
    """
    print("=" * 50)
    print("REPRICER AGENT — FULL PIPELINE RUN")
    print("=" * 50)
    print()

    # ── Phase 1: Monitoring Agent ──────────────────────
    print(">>> PHASE 1: Monitoring Agent (Scraping)")
    print("-" * 40)
    run_scraper()
    print()

    # ── Phase 2 & 3: For each product ─────────────────
    product_ids = get_all_product_ids()
    print(f">>> Processing {len(product_ids)} product(s)")
    print()

    results = {"updated": 0, "skipped": 0, "failed": 0}

    for product_id in product_ids:
        print("-" * 40)

        # Phase 2: Margin Agent — pricing decision
        print(">>> PHASE 2: Margin Agent (Pricing Decision)")
        recommendation = run_margin_agent(product_id)
        print()

        # Phase 3: Execution Agent — write changes
        print(">>> PHASE 3: Execution Agent (DB Write)")
        product, _ = get_product_with_latest_competitor_prices(product_id)

        if recommendation is None:
            print("No recommendation returned. Skipping.")
            results["failed"] += 1
            continue

        changed = run_execution_agent(product_id, recommendation, product)

        if changed:
            results["updated"] += 1
        else:
            results["skipped"] += 1

        print()

    # ── Summary ────────────────────────────────────────
    print("=" * 50)
    print("PIPELINE COMPLETE")
    print(f"  Products updated : {results['updated']}")
    print(f"  Products skipped : {results['skipped']}")
    print(f"  Products failed  : {results['failed']}")
    print("=" * 50)


if __name__ == "__main__":
    run_full_pipeline()