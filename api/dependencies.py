import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def get_db():
    """
    Returns a psycopg2 connection using RealDictCursor.
    
    RealDictCursor makes every row come back as a dictionary
    e.g. {"id": 1, "name": "Mouse"} instead of (1, "Mouse")
    This is important because FastAPI needs dicts to convert
    data to JSON automatically.
    """
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=psycopg2.extras.RealDictCursor
    )
    return conn