# 🏥 MediCart Pharmacy Management System — DBMS Project

A comprehensive, normalized **Database Management Systems (DBMS)** project built **100% in pure Python with SQLite 3**.  
Zero external dependencies required. Simply clone and run.

---

## 🚀 Quick Start

### 1. Initialize the Database (Schema, Triggers, Views & Seeds)
```bash
python init_db.py
```
This executes `schema.sql`, configures all 10 tables in 3NF, installs active triggers, creates virtual views, and populates realistic seed data.

### 2. Launch the Application & Web Interface
```bash
python app.py
```
*Or:*
```bash
python index.py
```
The application will start a local HTTP server on `http://localhost:8000/` and automatically open your default browser.

---

## 🔑 Default Login Credentials

| Role | Email | Password | Access Level |
|---|---|---|---|
| 👑 **Master Admin** | `master@medicart.com` | `master123` | Full Access + Can Create Admins + View Audit Logs |
| 🟢 **Head Pharmacist** | `admin@medicart.com` | `admin123` | Medicine & Supplier Management + Rx Queue + Reports |
| 🔵 **Customer** | `john@example.com` | `password123` | Catalog Browsing + Rx Upload + Cart + Order History |
| 🔵 **Customer 2** | `priya@example.com` | `customer123` | Customer Account |

---

## 🔍 Stored Data Inspector & Formatter

View all stored tables, views, and relationships in clean, sorted ASCII tables:

```bash
python view_db.py              # Overview dashboard & table stats
python view_db.py medicines    # Medicines catalog sorted by Category & ID
python view_db.py orders       # Orders with line items sorted chronologically
python view_db.py batches      # Stock batches sorted by expiry timeline
python view_db.py users        # Customers & Administrator accounts
python view_db.py views        # Execute and view all 6 SQL analytical views
python view_db.py all          # Complete formatted printout of all 10 tables
python view_db.py export       # Export all tables to DATABASE_EXPORT.md
```

You can also view the pre-generated [DATABASE_EXPORT.md](file:///c:/Users/mohds/Desktop/python_prjct/DATABASE_EXPORT.md) file directly in your editor for clean Markdown tables of all 10 database entities!

---

## 📁 Project Structure

```
python_prjct/
├── schema.sql              # Complete 3NF DDL, Constraints, Indexes, Triggers, Views & Seeds
├── queries.sql             # Comprehensive SQL Queries suite (Joins, Aggregates, Subqueries, ACID)
├── init_db.py              # Standalone Python script to initialize & verify SQLite database
├── view_db.py              # Visual CLI Database Inspector (Clean tables, sorting, summaries)
├── app.py                  # Primary entry point launcher
├── index.py                # Pure Python HTTP Server, REST API & Complete 10-Page Web Interface
├── pharmacy_dbms.db        # SQLite 3 Relational Database file (auto-generated)
├── DATABASE_EXPORT.md      # Clean, human-readable Markdown export of all 10 tables & views
├── DBMS_PROJECT_REPORT.md  # Detailed Academic & Technical Project Report (ER, 3NF, Data Dictionary, Viva Q&A)
└── README.md               # Quickstart and overview guide
```

---

## 📊 Database Architecture (10 Normalized Tables in 3NF)

1. **`categories`** — Drug therapeutic classifications (`pain`, `antibiotics`, `vitamins`, `skincare`, `babycare`, `personalcare`).
2. **`users`** — Customer accounts with salted SHA-256 password security.
3. **`admins`** — Administrative staff accounts with `is_master` privilege flag.
4. **`medicines`** — Pharmaceutical catalog with Foreign Key to `categories`, pricing, stock, and Rx requirements.
5. **`orders`** — Customer orders with lifecycle tracking (`Placed`, `Confirmed`, `Shipped`, `Delivered`).
6. **`order_items`** — Weak associative entity resolving M:N relationship between Orders and Medicines.
7. **`prescriptions`** — Prescription upload records linked to patients and pharmacist verification queues.
8. **`suppliers`** — Medicine manufacturers and distributors contact ledger.
9. **`stock_batches`** — Batch tracking with expiry dates and inventory status (`ok`, `low`, `expiring`, `out`).
10. **`audit_log`** — Immutable audit trail of all transactions and administrative modifications.

---

## 💡 DBMS Features Highlighted
- **Normalization:** Evaluated and proved up to Third Normal Form (3NF).
- **Referential Integrity:** `FOREIGN KEY` constraints enforced via `PRAGMA foreign_keys = ON;` with `CASCADE` / `RESTRICT` rules.
- **Database Triggers:**
  - `trg_reduce_stock_after_order`: Automatically updates inventory balances when an order is placed.
  - `trg_order_placed_audit`: Automatically writes order placement records to `audit_log`.
  - `trg_user_signup_audit` & `trg_admin_create_audit`: Automatically audits registration events.
  - `trg_update_batch_status`: Automatically changes batch status to `'out'` upon stock depletion.
- **Virtual Views:**
  - `v_medicine_inventory`: Joins medicines with category names and icons.
  - `v_order_summary`: Aggregates line items, quantities, and order totals.
  - `v_sales_by_category`: Calculates total units sold and revenue per category.
  - `v_stock_alerts`: Identifies depleted, expiring, or critical stock batches.
- **Security:** Salted cryptographic SHA-256 password hashing and role-based access control (RBAC).

---

## 🖥️ 10 Wireframe User Interface Pages
1. **Home Page** — Hero banner, live stats counters, categories grid, and trust pillars.
2. **Medicines Page** — Search, Category sidebar filter, Price slider, Rx filter, and Sort dropdown.
3. **Medicine Detail Page** — Product specifications, dosage info, quantity selector, and buy actions.
4. **Prescriptions Page** — Document upload dropzone and verification tracking table.
5. **Shopping Cart Page** — Quantity steppers, real-time subtotals, and delivery charges.
6. **Checkout Page** — Recipient address, time slots, payment method selection (Card, UPI, COD).
7. **Orders & Tracking Page** — Order history with 4-stage visual delivery status progress tracker.
8. **Login / Sign Up Page** — Tabbed customer registration & authentication with quick-demo logins.
9. **About Us Page** — Technical overview, DBMS architecture, and team contact prompts.
10. **Contact Page** — Inquiry form with corporate office details.
*Plus:*
- **👑 Master Admin Dashboard** — Database table inspector, create new admins panel, system audit log.
- **🟢 Pharmacist Management** — Live sales & stock reports, medicine manager, supplier manager.
