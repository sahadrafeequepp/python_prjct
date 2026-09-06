-- ====================================================================
-- MediCart Pharmacy Management System — DBMS Project SQL Queries
-- Course / Laboratory SQL Query Demonstration Suite
-- Target DBMS: SQLite 3 / Standard SQL
-- ====================================================================

-- --------------------------------------------------------------------
-- SECTION 1: DATA DEFINITION & TABLE INSPECTION
-- --------------------------------------------------------------------

-- 1.1 List all user tables in the database
SELECT name, type 
FROM sqlite_master 
WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%'
ORDER BY type, name;

-- 1.2 Inspect table schema and column types for 'medicines'
PRAGMA table_info(medicines);

-- 1.3 Verify Foreign Key integrity enforcement
PRAGMA foreign_keys;

-- --------------------------------------------------------------------
-- SECTION 2: BASIC SELECT, FILTERING, SORTING & OPERATORS
-- --------------------------------------------------------------------

-- 2.1 Retrieve all medicines that require a prescription (Rx)
SELECT id, name, price, stock, manufacturer 
FROM medicines 
WHERE rx_required = 1;

-- 2.2 Find medicines priced between ₹50 and ₹200 sorted by price descending
SELECT id, name, price, stock 
FROM medicines 
WHERE price BETWEEN 50.0 AND 200.0 
ORDER BY price DESC;

-- 2.3 Search medicines containing 'relief' or 'drops' (Pattern matching)
SELECT id, name, manufacturer, price 
FROM medicines 
WHERE name LIKE '%Relief%' OR name LIKE '%Drops%';

-- 2.4 Find medicines manufactured by Sun Pharma, Cipla, or Abbott (IN operator)
SELECT id, name, manufacturer, price, stock 
FROM medicines 
WHERE manufacturer IN ('Sun Pharma', 'Cipla Ltd', 'Abbott Healthcare');

-- 2.5 Retrieve all stock batches that are either 'low' in quantity or 'expiring'
SELECT batch_no, medicine_id, quantity, expiry_date, status 
FROM stock_batches 
WHERE status IN ('low', 'expiring');

-- --------------------------------------------------------------------
-- SECTION 3: MULTI-TABLE JOINS (INNER JOIN, LEFT OUTER JOIN)
-- --------------------------------------------------------------------

-- 3.1 INNER JOIN: Display each medicine along with its Category Name and Icon
SELECT 
    m.id AS medicine_id,
    m.name AS medicine_name,
    c.name AS category_name,
    c.icon AS category_icon,
    m.price,
    m.stock
FROM medicines m
INNER JOIN categories c ON m.category_id = c.id
ORDER BY c.name, m.name;

-- 3.2 3-Table INNER JOIN: List complete line-item breakdown for every order
SELECT 
    o.id AS order_id,
    o.date AS order_date,
    o.delivery_name,
    m.name AS medicine_name,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) AS line_total
FROM orders o
INNER JOIN order_items oi ON o.id = oi.order_id
INNER JOIN medicines m ON oi.medicine_id = m.id
ORDER BY o.date DESC, o.id;

-- 3.3 LEFT OUTER JOIN: Stock batches with supplier details (handling NULL suppliers)
SELECT 
    sb.batch_no,
    m.name AS medicine_name,
    sb.quantity,
    sb.expiry_date,
    sb.status,
    COALESCE(s.name, 'Direct/Internal Stock') AS supplier_name,
    COALESCE(s.contact_person, 'N/A') AS supplier_contact
FROM stock_batches sb
INNER JOIN medicines m ON sb.medicine_id = m.id
LEFT OUTER JOIN suppliers s ON sb.supplier_id = s.id
ORDER BY sb.expiry_date ASC;

-- 3.4 LEFT JOIN: Identify categories that currently have ZERO orders placed
SELECT 
    c.id,
    c.name AS category_name,
    COUNT(oi.id) AS total_items_sold
FROM categories c
LEFT JOIN medicines m ON c.id = m.category_id
LEFT JOIN order_items oi ON m.id = oi.medicine_id
GROUP BY c.id, c.name
HAVING total_items_sold = 0;

-- --------------------------------------------------------------------
-- SECTION 4: AGGREGATE FUNCTIONS, GROUP BY & HAVING CLAUSES
-- --------------------------------------------------------------------

-- 4.1 Total Revenue, Total Orders, and Average Order Value
SELECT 
    COUNT(*) AS total_orders_placed,
    SUM(total) AS gross_revenue,
    ROUND(AVG(total), 2) AS average_order_value,
    MIN(total) AS min_order_value,
    MAX(total) AS max_order_value
FROM orders
WHERE status != 'Cancelled';

-- 4.2 Category-wise Sales Analysis (Units Sold and Revenue)
SELECT 
    c.id AS category_id,
    c.name AS category_name,
    COUNT(DISTINCT oi.order_id) AS distinct_orders,
    SUM(oi.quantity) AS units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_sales_revenue
FROM categories c
JOIN medicines m ON m.category_id = c.id
JOIN order_items oi ON oi.medicine_id = m.id
GROUP BY c.id, c.name
ORDER BY total_sales_revenue DESC;

-- 4.3 Top 5 Best Selling Medicines (by units sold) with HAVING filter
SELECT 
    m.id,
    m.name AS medicine_name,
    m.manufacturer,
    SUM(oi.quantity) AS total_units_sold,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
FROM medicines m
JOIN order_items oi ON m.id = oi.medicine_id
GROUP BY m.id, m.name, m.manufacturer
HAVING total_units_sold > 0
ORDER BY total_units_sold DESC
LIMIT 5;

-- 4.4 Orders Breakdown by Status
SELECT 
    status,
    COUNT(*) AS order_count,
    ROUND(SUM(total), 2) AS total_amount
FROM orders
GROUP BY status
ORDER BY order_count DESC;

-- 4.5 Suppliers with Total Batches Supplied and Inventory Quantity
SELECT 
    s.id AS supplier_id,
    s.name AS supplier_name,
    COUNT(sb.id) AS batches_supplied,
    COALESCE(SUM(sb.quantity), 0) AS total_units_in_stock
FROM suppliers s
LEFT JOIN stock_batches sb ON s.id = sb.supplier_id
GROUP BY s.id, s.name
ORDER BY total_units_in_stock DESC;

-- --------------------------------------------------------------------
-- SECTION 5: SUBQUERIES (CORRELATED, NESTED, AND EXISTS)
-- --------------------------------------------------------------------

-- 5.1 Scalar Subquery: Find medicines priced above the overall catalog average
SELECT 
    id, 
    name, 
    price, 
    (SELECT ROUND(AVG(price), 2) FROM medicines) AS catalog_avg_price,
    ROUND(price - (SELECT AVG(price) FROM medicines), 2) AS price_difference
FROM medicines
WHERE price > (SELECT AVG(price) FROM medicines)
ORDER BY price DESC;

-- 5.2 Nested Subquery with IN: Customers who have placed at least one delivered order
SELECT id, name, email, phone 
FROM users 
WHERE email IN (
    SELECT DISTINCT user_email 
    FROM orders 
    WHERE status = 'Delivered'
);

-- 5.3 Correlated Subquery: For each category, find the most expensive medicine
SELECT m.id, m.name, m.category_id, m.price
FROM medicines m
WHERE m.price = (
    SELECT MAX(m2.price)
    FROM medicines m2
    WHERE m2.category_id = m.category_id
);

-- 5.4 Subquery with EXISTS: Suppliers who have supplied at least one expiring batch
SELECT s.id, s.name, s.contact_person, s.phone 
FROM suppliers s
WHERE EXISTS (
    SELECT 1 
    FROM stock_batches sb 
    WHERE sb.supplier_id = s.id AND sb.status = 'expiring'
);

-- --------------------------------------------------------------------
-- SECTION 6: VIEW QUERIES & TRIGGER VERIFICATION
-- --------------------------------------------------------------------

-- 6.1 Query virtual table 'v_medicine_inventory'
SELECT * FROM v_medicine_inventory WHERE stock < 50;

-- 6.2 Query virtual table 'v_order_summary'
SELECT * FROM v_order_summary WHERE grand_total > 300;

-- 6.3 Query virtual table 'v_sales_by_category'
SELECT * FROM v_sales_by_category ORDER BY total_revenue DESC;

-- 6.4 Query virtual table 'v_stock_alerts'
SELECT * FROM v_stock_alerts;

-- 6.5 Inspect Audit Trail generated by Triggers
SELECT 
    id, 
    timestamp, 
    action, 
    entity, 
    entity_id, 
    user_email, 
    user_type, 
    details
FROM audit_log
ORDER BY timestamp DESC
LIMIT 10;

-- --------------------------------------------------------------------
-- SECTION 7: TRANSACTION MANAGEMENT (ACID DEMONSTRATION)
-- Demonstrating Atomic Order Placement with Stock Reduction & Rollback Safety
-- --------------------------------------------------------------------

-- Simulating Atomic Checkout:
BEGIN TRANSACTION;

-- Step 1: Insert new order header
INSERT INTO orders (id, user_email, date, total, status, delivery_name, delivery_address, delivery_phone, time_slot, payment_method)
VALUES ('ORD-9999', 'john@example.com', date('now', 'localtime'), 180.0, 'Placed', 'John Doe', '44, Lotus Residency, Kochi', '+91 98765 43210', 'Morning (9 AM - 12 PM)', 'UPI / Online');

-- Step 2: Insert order item (Trigger 'trg_reduce_stock_after_order' automatically reduces medicine stock!)
INSERT INTO order_items (order_id, medicine_id, quantity, unit_price)
VALUES ('ORD-9999', 1, 2, 45.0);

INSERT INTO order_items (order_id, medicine_id, quantity, unit_price)
VALUES ('ORD-9999', 6, 1, 90.0);

-- Step 3: Verify the reduction
SELECT id, name, stock FROM medicines WHERE id IN (1, 6);

-- Step 4: Commit transaction permanently
COMMIT;

-- Clean-up demo transaction
DELETE FROM order_items WHERE order_id = 'ORD-9999';
DELETE FROM orders WHERE id = 'ORD-9999';
UPDATE medicines SET stock = stock + 2 WHERE id = 1;
UPDATE medicines SET stock = stock + 1 WHERE id = 6;
