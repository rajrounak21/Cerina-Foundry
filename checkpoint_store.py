from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from db.config import get_connection_string
from contextlib import contextmanager
import atexit

# Global connection pool
_pool = None

def get_pool():
    global _pool
    if _pool is None:
        connection_string = get_connection_string()
        # Initialize the pool with proper connection management
        # - min_size: minimum connections to keep alive
        # - max_size: maximum concurrent connections
        # - max_idle: recycle connections idle for more than 5 minutes (300 seconds)
        # - timeout: wait up to 30 seconds for a connection
        # - check: validate connection health before returning it
        _pool = ConnectionPool(
            conninfo=connection_string,
            min_size=2,
            max_size=20,
            max_idle=300,  # Close connections idle for 5+ minutes
            timeout=30,
            check=ConnectionPool.check_connection  # Validate connections before use
        )
        
        # Ensure tables are created once at startup
        with _pool.connection() as conn:
            conn.autocommit = True
            checkpointer = PostgresSaver(conn)
            checkpointer.setup()
            
    return _pool

@contextmanager
def get_checkpointer_context():
    """
    Context manager that yields a PostgresSaver with a dedicated connection from the pool.
    Usage:
        with get_checkpointer_context() as checkpointer:
            graph = build_graph(checkpointer)
            graph.invoke(...)
    """
    pool = get_pool()
    with pool.connection() as conn:
        # conn.autocommit = True  # PostgresSaver usually handles transactions, but safe ensuring it works
        yield PostgresSaver(conn)

def close_pool():
    global _pool
    if _pool is not None:
        _pool.close()

atexit.register(close_pool)
