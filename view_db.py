"""
MediCart Pharmacy DBMS — Stored Data Inspector & Formatter
==========================================================
Visual CLI inspector that presents all tables, views, and records 
in pharmacy_dbms.db cleanly sorted, aligned, and easily understandable.

Usage:
    python view_db.py              # Overview dashboard & table stats
    python view_db.py all          # Print all 10 tables cleanly formatted
    python view_db.py medicines    # View medicines sorted by category & ID
    python view_db.py orders       # View orders with item breakdown sorted by date
    python view_db.py batches      # View stock batches sorted by expiry date
    python view_db.py users        # View customers and administrators
    python view_db.py views        # View all 6 analytical SQL views
    python view_db.py export       # Generate DATABASE_EXPORT.md with Markdown tables
"""
import os
import sys
import sqlite3
from datetime import datetime

# Ensure safe UTF-8 terminal output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'pharmacy_dbms.db')

def get_connection():
    if not os.path.exists(DB_PATH):
        print(f"[ERROR] Database file '{DB_PATH}' not found. Please run 'python init_db.py' first.")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def print_table(title, headers, rows, alignments=None):
    """Prints a clean ASCII table with custom alignments ('<', '>', '^')."""
    if not alignments:
        alignments = ['<'] * len(headers)
    
    # Calculate column widths based on headers and row values
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            str_val = str(val) if val is not None else 'NULL'
            if len(str_val) > col_widths[i]:
                col_widths[i] = len(str_val)
    
    # Extra padding
    col_widths = [w + 2 for w in col_widths]
    
    # Header bar
    total_width = sum(col_widths) + len(headers) + 1
    print(f"\n{'=' * total_width}")
    print(f"  {title.upper()}")
    print(f"{'=' * total_width}")
    
    # Column Header row
    hdr_cells = []
    for h, w, a in zip(headers, col_widths, alignments):
        if a == '>':
            hdr_cells.append(f"{h:>{w-1}} ")
        elif a == '^':
            hdr_cells.append(f"{h:^{w}}")
        else:
            hdr_cells.append(f" {h:<{w-1}}")
    print("|" + "|".join(hdr_cells) + "|")
    print("|" + "|".join(['-' * w for w in col_widths]) + "|")
    
    # Data Rows
    if not rows:
        empty_msg = "(No records found)"
        print(f"| {empty_msg:<{total_width-4}} |")
    else:
        for row in rows:
            cells = []
            for val, w, a in zip(row, col_widths, alignments):
                str_val = str(val) if val is not None else 'NULL'
                if a == '>':
                    cells.append(f"{str_val:>{w-1}} ")
                elif a == '^':
                    cells.append(f"{str_val:^{w}}")
                else:
                    cells.append(f" {str_val:<{w-1}}")
            print("|" + "|".join(cells) + "|")
            
    print(f"{'-' * total_width}")
    print(f"  Total records: {len(rows)}\n")

def show_overview(conn):
    print("=" * 76)
    print("  🏥 MEDICART PHARMACY DBMS — STORED DATA OVERVIEW DASHBOARD")
    print("=" * 76)
    print(f"  Database Path : {DB_PATH}")
    print(f"  Current Time  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 76)

    c = conn.cursor()
    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type = 'table' AND name NOT LIKE 'sqlite_%' 
        ORDER BY name;
    """)
    tables = [r[0] for r in c.fetchall()]

    table_rows = []
    total_rows = 0
    for idx, tbl in enumerate(tables, 1):
        c.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = c.fetchone()[0]
        total_rows += cnt
        
        # Primary key info
        c.execute(f"PRAGMA table_info({tbl})")
        pks = [col['name'] for col in c.fetchall() if col['pk']]
        pk_str = ", ".join(pks) if pks else "ROWID"
        
        table_rows.append([idx, tbl, cnt, pk_str])

    print_table(
        "10 Normalized Relational Tables (3NF)",
        ["#", "Table Name", "Records", "Primary Key"],
        table_rows,
        ["^", "<", ">", "<"]
    )

    # Key Metrics
    c.execute("SELECT COUNT(*) FROM medicines")
    med_count = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(stock), 0) FROM medicines")
    total_stock = c.fetchone()[0]
    c.execute("SELECT COUNT(*), COALESCE(SUM(total), 0) FROM orders")
    ord_count, ord_rev = c.fetchone()
    c.execute("SELECT COUNT(*) FROM users")
    cust_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM admins")
    admin_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM prescriptions WHERE status = 'Pending'")
    pending_rx = c.fetchone()[0]

    print("  📊 SYSTEM METRICS AT A GLANCE:")
    print(f"    • Total Medicine Catalog  : {med_count} items ({total_stock} units in inventory)")
    print(f"    • Total Orders Processed  : {ord_count} orders (Gross Revenue: ₹{ord_rev:,.2f})")
    print(f"    • Registered Customers    : {cust_count} active user accounts")
    print(f"    • System Administrators   : {admin_count} admins (1 Master Admin + 1 Pharmacist)")
    print(f"    • Pending Rx Verification : {pending_rx} prescriptions awaiting review")
    print("-" * 76)

    print("\n  🔍 HOW TO VIEW SPECIFIC SORTED TABLES:")
    print("    python view_db.py medicines    -> Medicines sorted by Category & ID")
    print("    python view_db.py orders       -> Orders sorted chronologically with line items")
    print("    python view_db.py batches      -> Stock batches sorted by Expiry Date")
    print("    python view_db.py users        -> Customers & Admins")
    print("    python view_db.py views        -> Output of 6 Virtual SQL Analytical Views")
    print("    python view_db.py all          -> Display all 10 tables formatted")
    print("    python view_db.py export       -> Export cleanly formatted DATABASE_EXPORT.md")
    print("=" * 76 + "\n")

def show_medicines(conn):
    c = conn.cursor()
    c.execute("""
        SELECT 
            m.id,
            c.name AS category,
            m.name AS medicine_name,
            '₹' || printf('%.2f', m.price) AS price,
            m.stock,
            CASE WHEN m.rx_required = 1 THEN 'REQUIRED (Rx)' ELSE 'No (OTC)' END AS rx_req,
            m.rating || '★ (' || m.reviews || ')' AS rating_reviews,
            m.manufacturer
        FROM medicines m
        INNER JOIN categories c ON m.category_id = c.id
        ORDER BY c.id ASC, m.id ASC;
    """)
    rows = [list(r) for r in c.fetchall()]
    print_table(
        "Medicines Catalog (Sorted by Category ID & Medicine ID)",
        ["ID", "Category", "Medicine Name", "Price", "Stock", "Prescription", "Rating", "Manufacturer"],
        rows,
        ["^", "<", "<", ">", ">", "^", "<", "<"]
    )

def show_orders(conn):
    c = conn.cursor()
    c.execute("""
        SELECT 
            o.id AS order_id,
            o.date,
            o.delivery_name,
            o.user_email,
            '₹' || printf('%.2f', o.total) AS total,
            o.status,
            o.payment_method
        FROM orders o
        ORDER BY o.date DESC, o.id DESC;
    """)
    orders = c.fetchall()

    rows = []
    for o in orders:
        c.execute("""
            SELECT m.name || ' (x' || oi.quantity || ' @ ₹' || oi.unit_price || ')'
            FROM order_items oi
            INNER JOIN medicines m ON oi.medicine_id = m.id
            WHERE oi.order_id = ?
            ORDER BY oi.id ASC;
        """, (o['order_id'],))
        items_str = ", ".join([r[0] for r in c.fetchall()])
        rows.append([
            o['order_id'],
            o['date'],
            o['delivery_name'],
            o['total'],
            o['status'],
            o['payment_method'],
            items_str
        ])

    print_table(
        "Orders & Line Items (Sorted Chronologically: Date DESC, Order ID DESC)",
        ["Order ID", "Date", "Customer Name", "Total", "Status", "Payment", "Purchased Items"],
        rows,
        ["^", "^", "<", ">", "^", "<", "<"]
    )

def show_batches(conn):
    c = conn.cursor()
    c.execute("""
        SELECT 
            sb.batch_no,
            m.name AS medicine_name,
            c.name AS category,
            sb.quantity AS units,
            sb.expiry_date,
            UPPER(sb.status) AS status,
            COALESCE(s.name, 'Direct Supply') AS supplier,
            ROUND(JULIANDAY(sb.expiry_date) - JULIANDAY('now', 'localtime')) AS days_left
        FROM stock_batches sb
        INNER JOIN medicines m ON sb.medicine_id = m.id
        INNER JOIN categories c ON m.category_id = c.id
        LEFT JOIN suppliers s ON sb.supplier_id = s.id
        ORDER BY sb.expiry_date ASC, sb.quantity ASC;
    """)
    rows = []
    for r in c.fetchall():
        d = dict(r)
        days = int(d['days_left']) if d['days_left'] is not None else 0
        days_str = f"{days} days" if days > 0 else "EXPIRED"
        rows.append([
            d['batch_no'],
            d['medicine_name'],
            d['category'],
            d['units'],
            d['expiry_date'],
            days_str,
            d['status'],
            d['supplier']
        ])

    print_table(
        "Stock Batches & Expiry Timeline (Sorted by Expiry Date ASC)",
        ["Batch No", "Medicine Name", "Category", "Stock", "Expiry Date", "Days Left", "Status", "Supplier"],
        rows,
        ["^", "<", "<", ">", "^", ">", "^", "<"]
    )

def show_users_and_admins(conn):
    c = conn.cursor()
    c.execute("""
        SELECT 
            id,
            name,
            email,
            phone,
            role,
            CASE WHEN is_master = 1 THEN 'MASTER ADMIN (Full Privileges)' ELSE 'Standard Staff Admin' END AS access,
            created_at
        FROM admins
        ORDER BY is_master DESC, id ASC;
    """)
    admin_rows = [list(r) for r in c.fetchall()]
    print_table(
        "Administrators (Sorted by Privilege: Master Admin First)",
        ["ID", "Name", "Email", "Phone", "Role", "Access Privileges", "Created At"],
        admin_rows,
        ["^", "<", "<", "<", "<", "<", "<"]
    )

    c.execute("""
        SELECT 
            u.id,
            u.name,
            u.email,
            u.phone,
            COUNT(o.id) AS total_orders,
            '₹' || printf('%.2f', COALESCE(SUM(o.total), 0.0)) AS total_spent,
            u.address
        FROM users u
        LEFT JOIN orders o ON u.email = o.user_email
        GROUP BY u.id
        ORDER BY u.id ASC;
    """)
    user_rows = [list(r) for r in c.fetchall()]
    print_table(
        "Customer Accounts (Sorted by Customer ID ASC)",
        ["ID", "Name", "Email", "Phone", "Orders Placed", "Total Spent", "Delivery Address"],
        user_rows,
        ["^", "<", "<", "<", ">", ">", "<"]
    )

def show_views(conn):
    c = conn.cursor()
    print("\n" + "=" * 76)
    print("  📊 DEMONSTRATION OF 6 ACTIVE VIRTUAL SQL VIEWS")
    print("=" * 76)

    # 1. Sales by Category
    c.execute("SELECT category_name, orders_count, total_units_sold, '₹' || printf('%.2f', total_revenue) FROM v_sales_by_category;")
    print_table("VIEW 1: v_sales_by_category (Pre-sorted by Revenue DESC)",
                ["Category", "Orders Count", "Units Sold", "Total Revenue"],
                [list(r) for r in c.fetchall()],
                ["<", ">", ">", ">"])

    # 2. Stock Alerts
    c.execute("SELECT batch_no, medicine_name, category_name, quantity, expiry_date, status, supplier_name FROM v_stock_alerts;")
    print_table("VIEW 2: v_stock_alerts (Depleted / Low / Expiring Batches)",
                ["Batch No", "Medicine", "Category", "Quantity", "Expiry Date", "Status", "Supplier"],
                [list(r) for r in c.fetchall()],
                ["^", "<", "<", ">", "^", "^", "<"])

    # 3. Customer Summary
    c.execute("SELECT customer_name, customer_email, total_orders, '₹' || printf('%.2f', total_spent), last_order_date FROM v_customer_summary;")
    print_table("VIEW 3: v_customer_summary (Customers Sorted by Total Spent DESC)",
                ["Customer Name", "Email", "Orders Placed", "Total Spent", "Last Order Date"],
                [list(r) for r in c.fetchall()],
                ["<", "<", ">", ">", "^"])

    # 4. Order Summary
    c.execute("SELECT order_id, order_date, delivery_name, status, total_items, total_units, '₹' || printf('%.2f', grand_total) FROM v_order_summary;")
    print_table("VIEW 4: v_order_summary (Orders Sorted by Date DESC)",
                ["Order ID", "Date", "Customer", "Status", "Items", "Units", "Grand Total"],
                [list(r) for r in c.fetchall()],
                ["^", "^", "<", "^", ">", ">", ">"])

def show_all_tables(conn):
    show_overview(conn)
    show_users_and_admins(conn)
    show_medicines(conn)
    show_batches(conn)
    show_orders(conn)

    # Suppliers
    c = conn.cursor()
    c.execute("SELECT id, name, contact_person, phone, email, categories, address FROM suppliers ORDER BY id ASC;")
    print_table("Suppliers (Sorted by ID)",
                ["ID", "Company Name", "Contact Person", "Phone", "Email", "Supplied Categories", "Address"],
                [list(r) for r in c.fetchall()],
                ["^", "<", "<", "<", "<", "<", "<"])

    # Prescriptions
    c.execute("SELECT id, filename, patient_name, doctor_name, date, status, order_id, notes FROM prescriptions ORDER BY date DESC, id DESC;")
    print_table("Prescriptions (Sorted by Date DESC)",
                ["ID", "Document File", "Patient Name", "Doctor Name", "Date", "Status", "Linked Order", "Pharmacist Notes"],
                [list(r) for r in c.fetchall()],
                ["^", "<", "<", "<", "^", "^", "^", "<"])

    # Audit Log
    c.execute("SELECT id, action, entity, entity_id, user_email, user_type, timestamp, details FROM audit_log ORDER BY id DESC LIMIT 15;")
    print_table("Audit Log (Most Recent 15 System Events - Sorted ID DESC)",
                ["ID", "Action", "Entity", "Target ID", "User Email", "Role", "Timestamp", "Event Details"],
                [list(r) for r in c.fetchall()],
                ["^", "<", "<", "^", "<", "^", "<", "<"])

def export_markdown(conn):
    out_file = os.path.join(BASE_DIR, 'DATABASE_EXPORT.md')
    c = conn.cursor()
    lines = []
    lines.append("# 🏥 MediCart Pharmacy Management System — Database Stored Data")
    lines.append(f"**Target DBMS:** SQLite 3 (`pharmacy_dbms.db`)  ")
    lines.append(f"**Export Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Normalization:** 3NF (Third Normal Form) | **Total Tables:** 10 | **Active Views:** 6  \n")
    lines.append("---\n")

    # Table of Contents
    lines.append("## 📑 Table of Contents")
    lines.append("1. [categories](#1-categories)")
    lines.append("2. [admins](#2-admins)")
    lines.append("3. [users](#3-users)")
    lines.append("4. [suppliers](#4-suppliers)")
    lines.append("5. [medicines](#5-medicines)")
    lines.append("6. [stock_batches](#6-stock_batches)")
    lines.append("7. [orders](#7-orders)")
    lines.append("8. [order_items](#8-order_items)")
    lines.append("9. [prescriptions](#9-prescriptions)")
    lines.append("10. [audit_log](#10-audit_log)")
    lines.append("11. [SQL Analytical Views](#11-sql-analytical-views)\n")
    lines.append("---\n")

    tables = [
        ('categories', 'SELECT id, slug, name, icon, description FROM categories ORDER BY id ASC;',
         ['ID', 'Slug', 'Name', 'Icon', 'Description']),
        ('admins', 'SELECT id, name, email, phone, role, is_master, created_at FROM admins ORDER BY is_master DESC, id ASC;',
         ['ID', 'Name', 'Email', 'Phone', 'Role', 'Is Master', 'Created At']),
        ('users', 'SELECT id, name, email, phone, address, created_at FROM users ORDER BY id ASC;',
         ['ID', 'Name', 'Email', 'Phone', 'Address', 'Created At']),
        ('suppliers', 'SELECT id, name, contact_person, phone, email, categories, address FROM suppliers ORDER BY id ASC;',
         ['ID', 'Name', 'Contact Person', 'Phone', 'Email', 'Categories', 'Address']),
        ('medicines', 'SELECT id, name, category_id, price, rating, reviews, stock, rx_required, manufacturer FROM medicines ORDER BY category_id ASC, id ASC;',
         ['ID', 'Medicine Name', 'Cat ID', 'Price (₹)', 'Rating', 'Reviews', 'Stock', 'Rx Required', 'Manufacturer']),
        ('stock_batches', 'SELECT id, medicine_id, batch_no, quantity, expiry_date, status, received_date, supplier_id FROM stock_batches ORDER BY expiry_date ASC;',
         ['ID', 'Med ID', 'Batch No', 'Quantity', 'Expiry Date', 'Status', 'Received Date', 'Supplier ID']),
        ('orders', 'SELECT id, user_email, date, total, status, delivery_name, delivery_phone, time_slot, payment_method FROM orders ORDER BY date DESC, id DESC;',
         ['Order ID', 'Customer Email', 'Date', 'Total (₹)', 'Status', 'Recipient', 'Phone', 'Time Slot', 'Payment']),
        ('order_items', 'SELECT id, order_id, medicine_id, quantity, unit_price FROM order_items ORDER BY order_id ASC, id ASC;',
         ['ID', 'Order ID', 'Med ID', 'Quantity', 'Unit Price (₹)']),
        ('prescriptions', 'SELECT id, filename, patient_name, doctor_name, date, status, order_id, user_email FROM prescriptions ORDER BY date DESC, id DESC;',
         ['ID', 'File Name', 'Patient Name', 'Doctor Name', 'Date', 'Status', 'Order ID', 'Customer Email']),
        ('audit_log', 'SELECT id, action, entity, entity_id, user_email, user_type, timestamp, details FROM audit_log ORDER BY id DESC LIMIT 20;',
         ['ID', 'Action', 'Entity', 'Entity ID', 'User Email', 'Role', 'Timestamp', 'Details'])
    ]

    for idx, (tbl_name, query, headers) in enumerate(tables, 1):
        c.execute(query)
        rows = c.fetchall()
        lines.append(f"### {idx}. `{tbl_name}`")
        lines.append(f"**Total records:** {len(rows)}  \n")
        
        # Markdown table
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(['---'] * len(headers)) + " |")
        for row in rows:
            clean_vals = [str(v).replace('|', '\\|') if v is not None else 'NULL' for v in row]
            lines.append("| " + " | ".join(clean_vals) + " |")
        lines.append("\n---\n")

    # Analytical Views
    lines.append("## 11. SQL Analytical Views\n")
    
    # View 1
    lines.append("### View: `v_sales_by_category`")
    c.execute("SELECT category_name, orders_count, total_units_sold, total_revenue FROM v_sales_by_category;")
    lines.append("| Category | Orders | Units Sold | Revenue (₹) |")
    lines.append("|---|---|---|---|")
    for r in c.fetchall():
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | ₹{r[3]:,.2f} |")
    lines.append("\n")

    # View 2
    lines.append("### View: `v_stock_alerts`")
    c.execute("SELECT batch_no, medicine_name, category_name, quantity, expiry_date, status, supplier_name FROM v_stock_alerts;")
    lines.append("| Batch No | Medicine | Category | Stock | Expiry Date | Status | Supplier |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in c.fetchall():
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {r[6]} |")
    lines.append("\n")

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n  [EXPORT COMPLETE] Generated clean Markdown document: {out_file}\n")

def main():
    conn = get_connection()
    try:
        arg = sys.argv[1].lower() if len(sys.argv) > 1 else 'overview'
        if arg in ('overview', 'summary', 'info'):
            show_overview(conn)
        elif arg in ('medicines', 'meds', 'catalog'):
            show_medicines(conn)
        elif arg in ('orders', 'sales'):
            show_orders(conn)
        elif arg in ('batches', 'stock', 'inventory'):
            show_batches(conn)
        elif arg in ('users', 'admins', 'customers', 'accounts'):
            show_users_and_admins(conn)
        elif arg in ('views', 'reports'):
            show_views(conn)
        elif arg in ('all', 'dump', 'full'):
            show_all_tables(conn)
        elif arg in ('export', 'markdown', 'md'):
            export_markdown(conn)
        else:
            print(f"Unknown command: '{arg}'. Options: overview, all, medicines, orders, batches, users, views, export")
    finally:
        conn.close()

if __name__ == '__main__':
    main()
