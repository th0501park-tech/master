import logging
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from app.core.config import settings

logger = logging.getLogger(__name__)

db_pool: pool.ThreadedConnectionPool | None = None

def init_db_pool(minconn: int = 1, maxconn: int = 10):
    global db_pool
    if db_pool is None:
        try:
            db_pool = pool.ThreadedConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                dsn=settings.DATABASE_URL
            )
            logger.info("Neon DB Connection Pool successfully initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Neon DB connection pool: {e}")
            raise e

def close_db_pool():
    global db_pool
    if db_pool is not None:
        db_pool.closeall()
        db_pool = None
        logger.info("Neon DB Connection Pool closed.")

@contextmanager
def get_db():
    """
    Context manager yielding a RealDictCursor.
    Automatically commits on normal exit, rolls back on error,
    and returns the connection to the pool.
    """
    global db_pool
    if db_pool is None:
        init_db_pool()

    conn = db_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)
