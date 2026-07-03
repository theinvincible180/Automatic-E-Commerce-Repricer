from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from api.dependencies import get_db

router = APIRouter(prefix="/products", tags=["Products"])


# ── Pydantic models ──────────────────────────────────────────
# These define the exact shape of data FastAPI expects in
# request bodies. FastAPI auto-validates and returns clear
# errors if data is wrong or missing.

class CompetitorURLIn(BaseModel):
    competitor_name: str
    url: str


class ProductCreate(BaseModel):
    name: str
    sku: str
    our_cost: float
    min_margin_percent: float
    max_price: Optional[float] = None
    current_price: float
    competitor_urls: list[CompetitorURLIn] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    our_cost: Optional[float] = None
    min_margin_percent: Optional[float] = None
    max_price: Optional[float] = None
    current_price: Optional[float] = None


# ── Endpoints ────────────────────────────────────────────────

@router.get("/")
def get_all_products():
    """
    Returns all products with their latest competitor prices.
    Main data source for the dashboard overview page.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, sku, our_cost, min_margin_percent,
               max_price, current_price, created_at
        FROM products
        ORDER BY name
    """)
    products = cur.fetchall()

    result = []
    for product in products:
        product = dict(product)

        # Get latest price from each competitor for this product
        cur.execute("""
            SELECT DISTINCT ON (competitor_name)
                competitor_name, scraped_price, scraped_at
            FROM competitor_prices
            WHERE product_id = %s
            ORDER BY competitor_name, scraped_at DESC
        """, (product["id"],))

        competitor_prices = [dict(r) for r in cur.fetchall()]
        product["competitor_prices"] = competitor_prices

        prices = [r["scraped_price"] for r in competitor_prices]
        product["lowest_competitor_price"] = float(min(prices)) if prices else None

        result.append(product)

    cur.close()
    conn.close()
    return result


@router.get("/{product_id}")
def get_product(product_id: int):
    """Returns a single product with competitor URLs."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, sku, our_cost, min_margin_percent,
               max_price, current_price, created_at
        FROM products WHERE id = %s
    """, (product_id,))

    product = cur.fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    product = dict(product)

    cur.execute("""
        SELECT id, competitor_name, url, is_active
        FROM competitor_urls
        WHERE product_id = %s
        ORDER BY competitor_name
    """, (product_id,))

    product["competitor_urls"] = [dict(r) for r in cur.fetchall()]

    cur.close()
    conn.close()
    return product


@router.post("/", status_code=201)
def create_product(data: ProductCreate):
    """
    Creates a new product and its competitor URLs atomically.
    RETURNING id gives us the new row's ID without a second query.
    """
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO products
                (name, sku, our_cost, min_margin_percent, max_price, current_price)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.name, data.sku, data.our_cost,
            data.min_margin_percent, data.max_price, data.current_price
        ))
        new_id = cur.fetchone()["id"]

        if data.competitor_urls:
            cur.executemany("""
                INSERT INTO competitor_urls (product_id, competitor_name, url)
                VALUES (%s, %s, %s)
            """, [(new_id, c.competitor_name, c.url) for c in data.competitor_urls])

        conn.commit()
        return {"id": new_id, "message": "Product created successfully."}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    finally:
        cur.close()
        conn.close()


@router.patch("/{product_id}")
def update_product(product_id: int, data: ProductUpdate):
    """
    Partial update — only fields that are sent get updated.
    PATCH = update some fields.
    PUT   = replace the whole record.
    We use PATCH so frontend can send just one changed field.
    """
    fields = {k: v for k, v in data.model_dump().items() if v is not None}

    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided.")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [product_id]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        f"UPDATE products SET {set_clause} WHERE id = %s RETURNING id",
        values
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Product not found.")

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Product updated."}


@router.delete("/{product_id}")
def delete_product(product_id: int):
    """
    Deletes a product. ON DELETE CASCADE in the schema
    automatically deletes all related competitor_prices,
    competitor_urls, and price_history rows too.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM products WHERE id = %s RETURNING id",
        (product_id,)
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Product not found.")

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Product deleted."}


@router.post("/{product_id}/competitor-urls", status_code=201)
def add_competitor_url(product_id: int, data: CompetitorURLIn):
    """Adds a new competitor URL to an existing product."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO competitor_urls (product_id, competitor_name, url)
        VALUES (%s, %s, %s) RETURNING id
    """, (product_id, data.competitor_name, data.url))

    new_id = cur.fetchone()["id"]
    conn.commit()
    cur.close()
    conn.close()
    return {"id": new_id, "message": "Competitor URL added."}


@router.delete("/competitor-urls/{url_id}")
def delete_competitor_url(url_id: int):
    """Removes a competitor URL by its ID."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM competitor_urls WHERE id = %s RETURNING id",
        (url_id,)
    )
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="URL not found.")

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Competitor URL deleted."}