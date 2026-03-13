#!/usr/bin/env python3
"""
Concept: Database Connection and Simple Query
Description: Use SQLAlchemy to connect to a database and run a simple query.
Note: Assumes a running PostgreSQL instance. Set DATABASE_URL env var.
"""

import os
from sqlalchemy import create_engine, text

def main():
    # Get database URL from env (fallback to SQLite for demo)
    db_url = os.getenv("DATABASE_URL", "sqlite:///demo.db")
    engine = create_engine(db_url)

    # Create a simple table if it doesn't exist
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                age INTEGER
            )
        """))
        # Insert sample data
        conn.execute(text("INSERT OR IGNORE INTO users (id, name, age) VALUES (1, 'Alice', 25)"))
        conn.execute(text("INSERT OR IGNORE INTO users (id, name, age) VALUES (2, 'Bob', 30)"))

    # Query data
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM users"))
        rows = result.fetchall()
        print("Users in database:")
        for row in rows:
            print(row)

if __name__ == "__main__":
    main()