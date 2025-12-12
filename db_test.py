import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to your postgres DB
Connection= os.getenv("POSTGRES_URL")
conn = psycopg2.connect(Connection)
print("Connection successful")

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a query
cur.execute("""CREATE TABLE IF NOT EXISTS users(
id SERIAL PRIMARY KEY,
name TEXT,
age INT
);
""")
conn.commit()

cur.execute("""INSERT INTO users(name, age) VALUES('Rounak', 20);""")
conn.commit()

cur.execute("""SELECT * FROM users;""")
rows = cur.fetchall()
for row in rows:
    print(row)

# Close communication with the database
cur.close()
conn.close()