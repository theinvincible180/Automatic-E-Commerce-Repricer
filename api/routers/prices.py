from fastapi import APIRouter
from api.dependencies import get_db

router = APIRouter(tags=["Prices"])


@router.get("/products/{product_id}/price-history")
def get_price_history(product_id: int, limit: int = 50):
    """
    Returns price change history for a product.
    ?limit=30 lets the frontend control how many records to fetch.
    We reverse the list so charts show oldest → newest left to right.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, old_price, new_price, reason, changed_at
        FROM price_history
        WHERE product_id = %s
        ORDER BY changed_at DESC
        LIMIT %s
    """, (product_id, limit))

    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return list(reversed(rows))


@router.get("/products/{product_id}/competitor-prices")
def get_competitor_price_history(product_id: int, limit: int = 100):
    """
    Returns recent competitor price scrapes for a product.
    Used to draw competitor price trend lines on the dashboard chart.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT competitor_name, scraped_price, scraped_at
        FROM competitor_prices
        WHERE product_id = %s
        ORDER BY scraped_at DESC
        LIMIT %s
    """, (product_id, limit))

    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return list(reversed(rows))


@router.get("/alerts")
def get_alerts(threshold_percent: float = 10.0):
    """
    Returns products where the most recent price change
    exceeded threshold_percent. Powers the alerts panel.
    
    NULLIF(old_price, 0) prevents division by zero errors
    in the percentage calculation.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT ON (ph.product_id)
            p.name,
            ph.product_id,
            ph.old_price,
            ph.new_price,
            ph.reason,
            ph.changed_at,
            ABS(ph.new_price - ph.old_price) 
                / NULLIF(ph.old_price, 0) * 100 AS change_percent
        FROM price_history ph
        JOIN products p ON ph.product_id = p.id
        ORDER BY ph.product_id, ph.changed_at DESC
    """)

    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()

    alerts = [
        r for r in rows
        if r["change_percent"] and float(r["change_percent"]) >= threshold_percent
    ]
    return sorted(alerts, key=lambda x: x["changed_at"], reverse=True)