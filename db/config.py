import os
from psycopg2 import connect
from dotenv import load_dotenv

load_dotenv()

# Use POSTGRES_URL from .env
DATABASE_URL = os.getenv("POSTGRES_URL")

def get_db_connection():
    """Get a psycopg2 connection to the database"""
    return connect(DATABASE_URL)

def get_connection_string():
    """Get the raw connection string for LangGraph"""
    return DATABASE_URL
