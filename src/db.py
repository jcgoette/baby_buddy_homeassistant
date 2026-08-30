import os
import psycopg2

def connect_db():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "buddy"),
        password=os.getenv("DB_PASSWORD", "secret"),
        dbname=os.getenv("DB_NAME", "buddydb")
    )
    print("Connected to Postgres!")
    return conn

