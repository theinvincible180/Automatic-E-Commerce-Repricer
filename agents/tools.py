import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.tools import tool
from scraper import run_scraper
from margin_agent import get_product_with_latest_competitor_prices
from pricing_engine import decide_optimal_price
from execution_agent import validate_recommendation, update_product_price
import psycopg2
from dotenv import load_dotenv

load_dotenv()


@tool
def scrape_competitor_prices_tool(dummy: str = "") -> str:
    """
    Scrapes all active competitor URLs in the database and saves
    the latest prices to the competitor_prices table.
    Returns a summary confirming scraping is complete.
    Use this tool first at the start of every repricing cycle.
    """
    try:
        run_scraper()
        return "Scraping complete. All competitor prices saved to database."
    except Exception as e:
        return f"Scraping failed: {str(e)}"


@tool
def get_all_product_ids_tool(dummy: str = "") -> str:
    """
    Returns a list of all product IDs and names in the database.
    Use this to know which products need to be repriced.
    """
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM products")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            return "No products found in database."

        result = "Products in database:\n"
        for pid, name in rows:
            result += f"  ID {pid}: {name}\n"
        return result.strip()
    except Exception as e:
        return f"Error fetching products: {str(e)}"


@tool
def get_product_pricing_data_tool(product_id: str) -> str:
    """
    Given a product_id, retrieves the product's cost, margin rules,
    current price, and latest scraped competitor prices.
    Use this before making any pricing decisions.
    Input: product_id as a string e.g. "1"
    """
    try:
        pid = int(product_id.strip())
        product, competitor_rows = get_product_with_latest_competitor_prices(pid)

        if not product:
            return f"No product found with ID {product_id}."

        prod_id, name, our_cost, min_margin, max_price, current_price = product

        summary = f"""
Product ID     : {prod_id}
Name           : {name}
Our Cost       : £{our_cost}
Min Margin     : {min_margin}%
Max Price      : £{max_price or 'none'}
Current Price  : £{current_price}

Competitor Prices:
"""
        if competitor_rows:
            for comp_name, price in competitor_rows:
                summary += f"  {comp_name}: £{price}\n"
        else:
            summary += "  No competitor prices available yet.\n"

        return summary.strip()
    except Exception as e:
        return f"Error retrieving product data: {str(e)}"


@tool
def calculate_optimal_price_tool(product_id: str) -> str:
    """
    Given a product_id, calculates the optimal competitive price
    applying margin floor, ceiling constraints, and undercut logic.
    Returns the recommended price and full reasoning.
    Use this after getting product pricing data.
    Input: product_id as a string e.g. "1"
    """
    try:
        pid = int(product_id.strip())
        product, competitor_rows = get_product_with_latest_competitor_prices(pid)

        if not product:
            return f"No product found with ID {product_id}."

        prod_id, name, our_cost, min_margin, max_price, current_price = product
        competitor_prices = [float(row[1]) for row in competitor_rows]

        recommendation = decide_optimal_price(
            our_cost=float(our_cost),
            min_margin_percent=float(min_margin),
            max_price=float(max_price) if max_price else None,
            current_price=float(current_price),
            competitor_prices=competitor_prices,
        )

        return f"""
Pricing Analysis for: {name}
Price Floor       : £{recommendation['price_floor']}
Lowest Competitor : £{recommendation['lowest_competitor']}
Target Price      : £{recommendation['target_price']}
Recommended Price : £{recommendation['recommended_price']}
Reason            : {recommendation['decision_reason']}
Action Needed     : {'YES - price should be updated' if recommendation['action_needed'] else 'NO - price is already optimal'}
""".strip()
    except Exception as e:
        return f"Error calculating price: {str(e)}"


@tool
def execute_price_update_tool(product_id: str) -> str:
    """
    Given a product_id, validates and executes a price update
    in the database if the recommended price differs from current.
    Also writes an audit record to price_history.
    Only call this after calculating the optimal price.
    Input: product_id as a string e.g. "1"
    """
    try:
        pid = int(product_id.strip())
        product, competitor_rows = get_product_with_latest_competitor_prices(pid)

        if not product:
            return f"No product found with ID {product_id}."

        prod_id, name, our_cost, min_margin, max_price, current_price = product
        competitor_prices = [float(row[1]) for row in competitor_rows]

        recommendation = decide_optimal_price(
            our_cost=float(our_cost),
            min_margin_percent=float(min_margin),
            max_price=float(max_price) if max_price else None,
            current_price=float(current_price),
            competitor_prices=competitor_prices,
        )

        if not recommendation.get("action_needed"):
            return f"No price change needed for {name}. Current price £{current_price} is already optimal."

        is_valid, validation_msg = validate_recommendation(recommendation, product)
        if not is_valid:
            return f"Price update refused for {name}. Reason: {validation_msg}"

        new_price = recommendation["recommended_price"]
        reason = recommendation["decision_reason"]
        old_price = update_product_price(pid, new_price, reason)

        return (
            f"Price updated successfully for {name}.\n"
            f"  Old price : £{old_price}\n"
            f"  New price : £{new_price}\n"
            f"  Reason    : {reason}"
        )
    except Exception as e:
        return f"Error executing price update: {str(e)}"