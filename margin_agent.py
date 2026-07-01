import os
from dotenv import load_dotenv
import psycopg2
from pricing_engine import decide_optimal_price

load_dotenv()


def get_product_with_latest_competitor_prices(product_id):
    """
    Fetch a product's cost/margin rules AND
    the most recent scraped price from each competitor.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, our_cost, min_margin_percent, max_price, current_price
        FROM products
        WHERE id = %s
    """, (product_id,))
    product = cur.fetchone()

    if not product:
        cur.close()
        conn.close()
        return None, []

    
    cur.execute("""
        SELECT DISTINCT ON (competitor_name) 
            competitor_name, scraped_price
        FROM competitor_prices
        WHERE product_id = %s
        ORDER BY competitor_name, scraped_at DESC
    """, (product_id,))
    competitor_rows = cur.fetchall()

    cur.close()
    conn.close()

    return product, competitor_rows


def run_margin_agent(product_id):
    """
    Run the margin/risk check for a single product.
    Prints the full analysis and returns the recommendation.
    """
    print(f"=== Margin Agent: Product ID {product_id} ===\n")

    product, competitor_rows = get_product_with_latest_competitor_prices(product_id)

    if not product:
        print("Product not found.")
        return None

    prod_id, name, our_cost, min_margin, max_price, current_price = product

    print(f"Product       : {name}")
    print(f"Our Cost      : £{our_cost}")
    print(f"Min Margin    : {min_margin}%")
    print(f"Max Price     : £{max_price or 'none'}")
    print(f"Current Price : £{current_price}")
    print()

    if competitor_rows:
        print("Latest competitor prices:")
        for comp_name, price in competitor_rows:
            print(f"  {comp_name}: £{price}")
    else:
        print("No competitor prices scraped yet.")
    print()

    competitor_prices = [float(row[1]) for row in competitor_rows]

    recommendation = decide_optimal_price(
        our_cost=float(our_cost),
        min_margin_percent=float(min_margin),
        max_price=float(max_price) if max_price else None,
        current_price=float(current_price),
        competitor_prices=competitor_prices,
    )

    print("--- Pricing Decision ---")
    print(f"Price Floor       : £{recommendation['price_floor']}")
    print(f"Lowest Competitor : £{recommendation['lowest_competitor']}")
    print(f"Target Price      : £{recommendation['target_price']}")
    print(f"Recommended Price : £{recommendation['recommended_price']}")
    print(f"Reason            : {recommendation['decision_reason']}")
    print(f"Action Needed     : {'YES' if recommendation['action_needed'] else 'NO (price unchanged)'}")
    return recommendation


if __name__ == "__main__":
    run_margin_agent(product_id=1)