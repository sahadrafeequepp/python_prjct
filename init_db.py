"""
MediCart Pharmacy Management System — Database Initializer
Executes schema.sql, populates seed data, verifies tables, and prints status.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'pharmacy_dbms.db')
SCHEMA_PATH = os.path.join(BASE_DIR, 'schema.sql')

def init_database(db_path=DB_PATH, schema_path=SCHEMA_PATH):
    print("=" * 72)
    print("  MEDICART PHARMACY DBMS PROJECT - DATABASE INITIALIZER")
    print("=" * 72)
    print(f"  Target Database : {db_path}")
    print(f"  Schema Script   : {schema_path}")
    print()

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Execute DDL, Views, Triggers and Seed Data
    print("  Executing schema.sql DDL, Triggers, Views & DML seeds...")
    conn.executescript(schema_sql)
    conn.commit()
    print("  [SUCCESS] Schema executed successfully!\n")

    # Table Inspection
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%' 
        ORDER BY name;
    """)
    tables = [row[0] for row in cursor.fetchall()]

    print("-" * 72)
    print(f"  {'#':<3} | {'Table Name':<20} | {'Record Count':<14} | {'Status':<12}")
    print("-" * 72)
    for idx, tbl in enumerate(tables, 1):
        cursor.execute(f"SELECT COUNT(*) FROM {tbl};")
        cnt = cursor.fetchone()[0]
        print(f"  {idx:<3} | {tbl:<20} | {cnt:<14} | {'OK (Seeded)':<12}")
    print("-" * 72)

    # Views Inspection
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type = 'view' 
        ORDER BY name;
    """)
    views = [row[0] for row in cursor.fetchall()]
    print(f"\n  [VIEWS] Active Virtual Views ({len(views)}):")
    for v in views:
        print(f"    - {v}")

    # Triggers Inspection
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type = 'trigger' 
        ORDER BY name;
    """)
    triggers = [row[0] for row in cursor.fetchall()]
    print(f"\n  [TRIGGERS] Active Triggers ({len(triggers)}):")
    for t in triggers:
        print(f"    - {t}")

    conn.close()

    print("\n" + "=" * 72)
    print("  DEFAULT LOGIN CREDENTIALS:")
    print("  ----------------------------------------------------------------------")
    print("  [Master Admin] : master@medicart.com  / master123  (is_master = 1)")
    print("  [Pharmacist]   : admin@medicart.com   / admin123   (is_master = 0)")
    print("  [Customer 1]   : john@example.com     / password123")
    print("  [Customer 2]   : priya@example.com    / customer123")
    print("=" * 72 + "\n")

if __name__ == '__main__':
    init_database()
