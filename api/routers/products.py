from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from api.dependencies import get_db
from api.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])


# ── Pydantic models ──────────────────────────────────────────

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
def get_all_products(user: dict = Depends(get_current_user)):
    """
    Returns all products belonging to the logged-in user,
    with their latest competitor prices attached.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, sku, our_cost, min_margin_percent,
               max_price, current_price, created_at
        FROM products
        WHERE user_id = %s
        ORDER BY name
    """, (user["user_id"],))
    products = cur.fetchall()

    result = []
    for product in products:
        product = dict(product)

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
def get_product(product_id: int, user: dict = Depends(get_current_user)):
    """Returns a single product with competitor URLs, scoped to this user."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name, sku, our_cost, min_margin_percent,
               max_price, current_price, created_at
        FROM products WHERE id = %s AND user_id = %s
    """, (product_id, user["user_id"]))

    product = cur.fetchone()
    if not product:
        cur.close()
        conn.close()
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
def create_product(data: ProductCreate, user: dict = Depends(get_current_user)):
    """Creates a new product owned by the logged-in user."""
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO products
                (name, sku, our_cost, min_margin_percent, max_price, current_price, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.name, data.sku, data.our_cost,
            data.min_margin_percent, data.max_price, data.current_price,
            user["user_id"]
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
def update_product(product_id: int, data: ProductUpdate,
                    user: dict = Depends(get_current_user)):
    """Partial update — only fields that are sent get updated. Scoped to owner."""
    fields = {k: v for k, v in data.model_dump().items() if v is not None}

    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided.")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [product_id, user["user_id"]]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        f"UPDATE products SET {set_clause} WHERE id = %s AND user_id = %s RETURNING id",
        values
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found.")

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Product updated."}


@router.delete("/{product_id}")
def delete_product(product_id: int, user: dict = Depends(get_current_user)):
    """
    Deletes a product owned by the logged-in user.
    ON DELETE CASCADE in the schema automatically deletes all related
    competitor_prices, competitor_urls, and price_history rows too.
    """
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM products WHERE id = %s AND user_id = %s RETURNING id",
        (product_id, user["user_id"])
    )
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found.")

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Product deleted."}


@router.post("/{product_id}/competitor-urls", status_code=201)
def add_competitor_url(product_id: int, data: CompetitorURLIn,
                        user: dict = Depends(get_current_user)):
    """Adds a new competitor URL to an existing product owned by this user."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM products WHERE id = %s AND user_id = %s",
                (product_id, user["user_id"]))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Product not found.")

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
def delete_competitor_url(url_id: int, user: dict = Depends(get_current_user)):
    """Removes a competitor URL by its ID, only if it belongs to this user's product."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM competitor_urls
        WHERE id = %s
        AND product_id IN (SELECT id FROM products WHERE user_id = %s)
        RETURNING id
    """, (url_id, user["user_id"]))

    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="URL not found.")

    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Competitor URL deleted."}