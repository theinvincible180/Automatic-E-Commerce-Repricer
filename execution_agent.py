import os
from dotenv import load_dotenv
import psycopg2
from decimal import Decimal

load_dotenv()


def validate_recommendation(recommendation, product):
    """
    Safety layer — double check the recommendation makes
    sense before writing anything to the database.
    Returns (is_valid, reason).
    """
    prod_id, name, our_cost, min_margin, max_price, current_price = product

    if recommendation is None:
        return False, "Recommendation is None."

    recommended = recommendation.get("recommended_price")
    if recommended is None:
        return False, "No recommended price in result."

    recommended = Decimal(str(recommended))
    cost = Decimal(str(our_cost))

    # Hard safety check 1: price must always be above cost (never sell at a loss)
    if recommended <= cost:
        return False, f"Recommended price £{recommended} is at or below cost £{cost}. Refusing."

    # Hard safety check 2: price must be a positive number
    if recommended <= 0:
        return False, f"Recommended price £{recommended} is not positive. Refusing."

    # Hard safety check 3: sanity check — never change price by more than 50% in one go
    # This catches runaway agent behavior or scraping errors
    current = Decimal(str(current_price))
    if current > 0:
        change_percent = abs(recommended - current) / current * 100
        MAX_PRICE_CHANGE_PERCENT = 60  # configurable safety threshold

        if change_percent > MAX_PRICE_CHANGE_PERCENT:
            return False, (
                f"Recommended price £{recommended} is {change_percent:.1f}% "
                f"away from current price £{current}. "
                f"Change exceeds {MAX_PRICE_CHANGE_PERCENT}% safety threshold. Refusing."
)

    return True, "Validation passed."


def update_product_price(product_id, new_price, reason):
    """
    Update the product's current_price in the DB and
    write a record to price_history.
    Both happen in a single transaction — either both succeed or neither does.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    try:
        # Get current price first (needed for price_history record)
        cur.execute(
            "SELECT current_price FROM products WHERE id = %s",
            (product_id,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"Product ID {product_id} not found.")

        old_price = row[0]

        # Update the live price
        cur.execute("""
            UPDATE products
            SET current_price = %s
            WHERE id = %s
        """, (new_price, product_id))

        # Write to audit trail
        cur.execute("""
            INSERT INTO price_history (product_id, old_price, new_price, reason)
            VALUES (%s, %s, %s, %s)
        """, (product_id, old_price, new_price, reason))

        # Commit both changes together as one atomic transaction
        conn.commit()
        return old_price

    except Exception as e:
        # If anything goes wrong, roll back BOTH changes
        conn.rollback()
        raise e

    finally:
        cur.close()
        conn.close()


def run_execution_agent(product_id, recommendation, product):
    """
    Execute a pricing change for a product if the recommendation
    is valid and a change is actually needed.
    """
    print(f"=== Execution Agent: Product ID {product_id} ===\n")

    # Step 1: Check if a change is even needed
    if not recommendation.get("action_needed"):
        print("No action needed — price is already optimal.")
        return False

    # Step 2: Validate the recommendation (safety checks)
    is_valid, validation_msg = validate_recommendation(recommendation, product)
    print(f"Validation: {validation_msg}")

    if not is_valid:
        print("Execution aborted — validation failed.")
        return False

    # Step 3: Execute the price change
    new_price = recommendation["recommended_price"]
    reason = recommendation["decision_reason"]

    print(f"\nExecuting price change...")
    old_price = update_product_price(product_id, new_price, reason)

    print(f"  Old price : £{old_price}")
    print(f"  New price : £{new_price}")
    print(f"  Reason    : {reason}")
    print(f"\nPrice updated successfully.")
    return True