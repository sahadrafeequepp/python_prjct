-- ====================================================================
-- MediCart Pharmacy Management System — DBMS Project Schema
-- Database Management Systems (DBMS) Laboratory / Course Project
-- Target DBMS: SQLite 3 / Standard SQL
-- Normalization: 3NF (Third Normal Form)
-- ====================================================================

PRAGMA foreign_keys = ON;

-- --------------------------------------------------------------------
-- 1. DROP EXISTING TABLES & VIEWS (For Clean Re-runs)
-- --------------------------------------------------------------------
DROP VIEW IF EXISTS v_batches_detailed;
DROP VIEW IF EXISTS v_customer_summary;
DROP VIEW IF EXISTS v_sales_by_category;
DROP VIEW IF EXISTS v_stock_alerts;
DROP VIEW IF EXISTS v_order_summary;
DROP VIEW IF EXISTS v_medicine_inventory;

DROP TRIGGER IF EXISTS trg_reduce_stock_after_order;
DROP TRIGGER IF EXISTS trg_order_placed_audit;
DROP TRIGGER IF EXISTS trg_user_signup_audit;
DROP TRIGGER IF EXISTS trg_admin_create_audit;
DROP TRIGGER IF EXISTS trg_update_batch_status;

DROP TABLE IF EXISTS audit_log;
DROP TABLE IF EXISTS stock_batches;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS medicines;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS categories;

-- ====================================================================
-- 2. TABLE DEFINITIONS (DDL with Constraints)
-- ====================================================================

-- TABLE 1: categories (Product categorization)
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT '💊',
    description TEXT NOT NULL DEFAULT ''
);

-- TABLE 2: users (Customer accounts)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    address TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- TABLE 3: admins (Administrative accounts with Master Admin privilege)
CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Pharmacist',
    is_master INTEGER NOT NULL DEFAULT 0 CHECK (is_master IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- TABLE 4: medicines (Inventory items with Category Foreign Key)
CREATE TABLE medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    rating REAL NOT NULL DEFAULT 4.5 CHECK (rating >= 0 AND rating <= 5.0),
    reviews INTEGER NOT NULL DEFAULT 0 CHECK (reviews >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    rx_required INTEGER NOT NULL DEFAULT 0 CHECK (rx_required IN (0, 1)),
    manufacturer TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- TABLE 5: orders (Customer orders with lifecycle tracking)
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    user_email TEXT NOT NULL,
    date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    total REAL NOT NULL CHECK (total >= 0),
    status TEXT NOT NULL DEFAULT 'Placed' CHECK (status IN ('Placed', 'Confirmed', 'Shipped', 'Delivered', 'Cancelled')),
    delivery_name TEXT NOT NULL DEFAULT '',
    delivery_address TEXT NOT NULL DEFAULT '',
    delivery_phone TEXT NOT NULL DEFAULT '',
    time_slot TEXT NOT NULL DEFAULT 'Standard (Anytime)',
    payment_method TEXT NOT NULL DEFAULT 'Cash on Delivery',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- TABLE 6: order_items (Weak Entity / M:N Bridge between Orders and Medicines)
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    medicine_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- TABLE 7: prescriptions (Prescription uploads linked to orders/patients)
CREATE TABLE prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    doctor_name TEXT NOT NULL,
    date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    status TEXT NOT NULL DEFAULT 'Pending' CHECK (status IN ('Pending', 'Verified', 'Rejected')),
    order_id TEXT NOT NULL DEFAULT '',
    user_email TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- TABLE 8: suppliers (Medicine manufacturers and distributors)
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact_person TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    categories TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- TABLE 9: stock_batches (Batch tracking, expiry, and supplier linkage)
CREATE TABLE stock_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    batch_no TEXT NOT NULL UNIQUE,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    expiry_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'low', 'expiring', 'out')),
    received_date TEXT NOT NULL DEFAULT (date('now', 'localtime')),
    supplier_id INTEGER,
    FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- TABLE 10: audit_log (Comprehensive system audit trail for security & compliance)
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    user_type TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    details TEXT NOT NULL DEFAULT ''
);

-- ====================================================================
-- 3. INDEXES (Performance Optimization on Frequent Lookups & Foreign Keys)
-- ====================================================================
CREATE INDEX idx_med_category ON medicines(category_id);
CREATE INDEX idx_med_name ON medicines(name);
CREATE INDEX idx_order_user ON orders(user_email);
CREATE INDEX idx_order_date ON orders(date);
CREATE INDEX idx_order_items_ord ON order_items(order_id);
CREATE INDEX idx_order_items_med ON order_items(medicine_id);
CREATE INDEX idx_batches_med ON stock_batches(medicine_id);
CREATE INDEX idx_batches_expiry ON stock_batches(expiry_date);
CREATE INDEX idx_audit_user ON audit_log(user_email);
CREATE INDEX idx_audit_time ON audit_log(timestamp);

-- ====================================================================
-- 4. DATABASE TRIGGERS (Automated Business Logic & Audit Automation)
-- ====================================================================

-- Trigger A: Automatically decrement medicine inventory when order item is inserted
CREATE TRIGGER trg_reduce_stock_after_order
AFTER INSERT ON order_items
FOR EACH ROW
BEGIN
    UPDATE medicines
    SET stock = MAX(0, stock - NEW.quantity)
    WHERE id = NEW.medicine_id;
END;

-- Trigger B: Automatically log order placement in audit_log
CREATE TRIGGER trg_order_placed_audit
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action, entity, entity_id, user_email, user_type, timestamp, details)
    VALUES (
        'CREATE_ORDER',
        'orders',
        NEW.id,
        NEW.user_email,
        'customer',
        datetime('now', 'localtime'),
        'Order total: ₹' || NEW.total || ' for ' || NEW.delivery_name
    );
END;

-- Trigger C: Automatically log user sign-up in audit_log
CREATE TRIGGER trg_user_signup_audit
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action, entity, entity_id, user_email, user_type, timestamp, details)
    VALUES (
        'USER_SIGNUP',
        'users',
        NEW.id,
        NEW.email,
        'customer',
        datetime('now', 'localtime'),
        'New customer registration: ' || NEW.name
    );
END;

-- Trigger D: Automatically log admin creation in audit_log
CREATE TRIGGER trg_admin_create_audit
AFTER INSERT ON admins
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (action, entity, entity_id, user_email, user_type, timestamp, details)
    VALUES (
        'CREATE_ADMIN',
        'admins',
        NEW.id,
        NEW.email,
        CASE WHEN NEW.is_master = 1 THEN 'master' ELSE 'admin' END,
        datetime('now', 'localtime'),
        'Role: ' || NEW.role || ' (Master=' || NEW.is_master || ')'
    );
END;

-- Trigger E: Automatically mark batch status as 'out' if quantity reaches 0
CREATE TRIGGER trg_update_batch_status
AFTER UPDATE OF quantity ON stock_batches
FOR EACH ROW
WHEN NEW.quantity = 0
BEGIN
    UPDATE stock_batches
    SET status = 'out'
    WHERE id = NEW.id;
END;

-- ====================================================================
-- 5. DATABASE VIEWS (Virtual Tables for Abstraction & Reporting)
-- ====================================================================

-- View 1: Complete Medicine Catalog with Category Name & Icon (Pre-sorted by Category & Medicine)
CREATE VIEW v_medicine_inventory AS
SELECT 
    m.id AS medicine_id,
    c.id AS category_id,
    c.name AS category_name,
    c.icon AS category_icon,
    m.name AS medicine_name,
    m.price,
    m.stock,
    m.rx_required,
    m.manufacturer,
    m.rating,
    m.reviews
FROM medicines m
INNER JOIN categories c ON m.category_id = c.id
ORDER BY c.id ASC, m.name ASC;

-- View 2: Complete Order Summary with Item Counts & Recipient Details (Pre-sorted chronologically DESC)
CREATE VIEW v_order_summary AS
SELECT 
    o.id AS order_id,
    o.date AS order_date,
    o.user_email,
    o.delivery_name,
    o.delivery_phone,
    o.delivery_address,
    o.status,
    o.payment_method,
    COUNT(oi.id) AS total_items,
    COALESCE(SUM(oi.quantity), 0) AS total_units,
    o.total AS grand_total
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id
ORDER BY o.date DESC, o.id DESC;

-- View 3: Sales Analytics by Medicine Category (Pre-sorted by Revenue DESC)
CREATE VIEW v_sales_by_category AS
SELECT 
    c.id AS category_id,
    c.name AS category_name,
    c.icon AS category_icon,
    COUNT(DISTINCT oi.order_id) AS orders_count,
    COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0.0) AS total_revenue
FROM categories c
LEFT JOIN medicines m ON m.category_id = c.id
LEFT JOIN order_items oi ON oi.medicine_id = m.id
GROUP BY c.id
ORDER BY total_revenue DESC;

-- View 4: Stock Alerts View (Critical/Expiring/Depleted Batches, sorted by Expiry Date)
CREATE VIEW v_stock_alerts AS
SELECT 
    sb.id AS batch_id,
    sb.batch_no,
    m.name AS medicine_name,
    c.name AS category_name,
    sb.quantity,
    sb.expiry_date,
    sb.status,
    COALESCE(s.name, 'Internal Supplier') AS supplier_name,
    COALESCE(s.phone, 'N/A') AS supplier_phone
FROM stock_batches sb
INNER JOIN medicines m ON sb.medicine_id = m.id
INNER JOIN categories c ON m.category_id = c.id
LEFT JOIN suppliers s ON sb.supplier_id = s.id
WHERE sb.status != 'ok' OR sb.quantity <= 15
ORDER BY sb.expiry_date ASC, sb.quantity ASC;

-- View 5: Customer Purchase Summary (Sorted by Total Spent DESC)
CREATE VIEW v_customer_summary AS
SELECT 
    u.id AS user_id,
    u.name AS customer_name,
    u.email AS customer_email,
    u.phone AS customer_phone,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.total), 0.0) AS total_spent,
    MAX(o.date) AS last_order_date
FROM users u
LEFT JOIN orders o ON u.email = o.user_email
GROUP BY u.id
ORDER BY total_spent DESC;

-- View 6: Detailed Stock Batches with Supplier & Category Link (Sorted by Expiry Date)
CREATE VIEW v_batches_detailed AS
SELECT 
    sb.id AS batch_id,
    sb.batch_no,
    m.name AS medicine_name,
    c.name AS category_name,
    sb.quantity,
    sb.expiry_date,
    sb.status,
    s.name AS supplier_name,
    sb.received_date
FROM stock_batches sb
INNER JOIN medicines m ON sb.medicine_id = m.id
INNER JOIN categories c ON m.category_id = c.id
LEFT JOIN suppliers s ON sb.supplier_id = s.id
ORDER BY sb.expiry_date ASC;

-- ====================================================================
-- 6. SAMPLE DATA SEEDING (DML) - LOGICALLY SORTED & STRUCTURED
-- Passwords are SHA-256 salted hashes with salt 'MediCart_DBMS_2026'
-- ====================================================================

-- 6.1 Categories (Sorted by Sequential ID 1 to 6)
INSERT INTO categories (id, slug, name, icon, description) VALUES
(1, 'pain',         'Pain Relief',        '💊', 'Analgesics, antipyretics, and anti-inflammatory drugs'),
(2, 'antibiotics',  'Antibiotics',        '🦠', 'Prescription antibacterial and anti-infective medications'),
(3, 'vitamins',     'Vitamins & Supps',   '💉', 'Essential multivitamins, minerals, and daily supplements'),
(4, 'skincare',     'Skin Care',          '🧴', 'Dermatological creams, lotions, and soothing gels'),
(5, 'babycare',     'Baby Care',          '🍼', 'Pediatric medicines, baby nutrition, and infant care'),
(6, 'personalcare', 'Personal Hygiene',   '🧼', 'Hand hygiene, antiseptics, and personal sanitizers');

-- 6.2 Admin Accounts (Master Admin first, followed by Pharmacists)
-- Master Admin: master@medicart.com / master123
-- Pharmacist:   admin@medicart.com  / admin123
INSERT INTO admins (id, name, email, phone, password_hash, role, is_master, created_at) VALUES
(1, 'Master Administrator', 'master@medicart.com', '+91 99000 00000', 'd2b33a7d05b583287b10814e213932376b5d9077740f902f902eb06bad4e45b0', 'Master Admin',    1, '2026-08-01 10:00:00'),
(2, 'Dr. Kavya Suresh',     'admin@medicart.com',  '+91 98450 99887', 'd60b310dbb7a9964278fdd200a31e38466f180d1bc2dde641ec926faa49bf579', 'Head Pharmacist', 0, '2026-08-05 11:30:00');

-- 6.3 Customer Users (Sorted by Customer ID)
-- John Doe:     john@example.com  / password123
-- Priya Sharma: priya@example.com / customer123
INSERT INTO users (id, name, email, phone, password_hash, address, created_at) VALUES
(1, 'John Doe',     'john@example.com',  '+91 98765 43210', '12fbfb05ed998faec27d6a0a331dfa4b7b474fac6b8d37e4a0c65b028828368d', '44, Lotus Residency, MG Road, Kochi, Kerala 682016', '2026-08-10 14:15:00'),
(2, 'Priya Sharma', 'priya@example.com', '+91 98412 34567', 'd18b3db5ea5640837ba18b12c4320427e661c22c82410b3a596a763390b98e8d', '12B, Marine Drive Towers, Ernakulam, Kerala 682011', '2026-08-15 09:45:00');

-- 6.4 Suppliers (Sorted by ID and Primary Domain)
INSERT INTO suppliers (id, name, contact_person, phone, email, categories, address, created_at) VALUES
(1, 'MedSupply Co.',         'Suresh Nair', '+91 98450 11223', 'suresh@medsupply.in',   'Pain Relief, Antibiotics',     'Plot 18, Industrial Estate, Kochi, Kerala',        '2026-08-01 09:00:00'),
(2, 'Wellness Distributors', 'Priya Menon', '+91 97460 22110', 'priya@wellnessdist.in', 'Vitamins & Supps, Hygiene',    '45, Commercial Road, Kozhikode, Kerala',          '2026-08-02 10:30:00'),
(3, 'CarePlus Traders',      'Arun Das',    '+91 94470 33987', 'arun@careplustraders.in','Skin Care, Baby Care',         '8, Technopark Avenue, Thiruvananthapuram, Kerala','2026-08-03 12:00:00');

-- 6.5 Medicines (Sorted sequentially: 2 per Category from Category 1 to 6)
-- IDs 1-2:   Category 1 (Pain Relief)
-- IDs 3-4:   Category 2 (Antibiotics)
-- IDs 5-6:   Category 3 (Vitamins & Supps)
-- IDs 7-8:   Category 4 (Skin Care)
-- IDs 9-10:  Category 5 (Baby Care)
-- IDs 11-12: Category 6 (Personal Hygiene)
INSERT INTO medicines (id, name, category_id, price, rating, reviews, stock, rx_required, manufacturer, description) VALUES
(1,  'Paracetamol 500mg',               1,  45.0, 4.8, 120, 240, 0, 'Apex Health',      'Relieves mild to moderate pain including headache, toothache, muscular ache, and feverish conditions.'),
(2,  'Ibuprofen 400mg',                 1,  60.0, 4.7,  98, 180, 0, 'Abbott Healthcare','Fast-acting non-steroidal anti-inflammatory drug (NSAID) for joint aches, arthritis, and fever.'),
(3,  'Amoxicillin 250mg',               2, 120.0, 4.6,  88,  60, 1, 'Sun Pharma',       'Broad-spectrum penicillin-class antibiotic for acute bacterial infections of ear, throat, and chest.'),
(4,  'Azithromycin 500mg (3 Tabs)',     2, 150.0, 4.5,  41,   0, 1, 'Cipla Ltd',        'Macrolide antibiotic used for respiratory tract infections and strep throat. Requires valid Rx.'),
(5,  'Vitamin C 1000mg Effervescent',   3, 180.0, 4.9, 210, 150, 0, 'Redoxon Labs',     'Immune support tablets enriched with Zinc and Antioxidants for daily stamina and vitality.'),
(6,  'Adult Multivitamin Gummies',      3, 220.0, 4.8, 134,  75, 0, 'NutraLife',        'Delicious fruit-flavored chewable gummies packed with Vitamin B-complex, D3, and Iron.'),
(7,  'Soothing Aloe Vera Gel 200ml',    4, 210.0, 4.5,  64,  90, 0, 'Nature Care',      '100% organic hydrating cooling gel for sunburns, minor cuts, skin irritation, and dryness.'),
(8,  'Moisturizing Sunscreen SPF 50',   4, 280.0, 4.7,  82, 120, 0, 'DermaShield',      'Broad-spectrum UVA/UVB protection enriched with Vitamin E and soothing Chamomile extract.'),
(9,  'Baby Colic Relief Drops 30ml',    5, 160.0, 4.4,  52,  40, 0, 'Himalaya Baby',    'Ayurvedic and pediatric formula designed to quickly soothe infantile colic, spasm, and gas.'),
(10, 'Zinc Oxide Diaper Rash Cream 50g',5, 140.0, 4.6,  59,  55, 0, 'Sebamed Baby',     'Gentle hypoallergenic protective barrier cream with panthenol for delicate baby skin.'),
(11, 'Antibacterial Hand Wash 250ml',   6,  95.0, 4.3,  73, 200, 0, 'Dettol Herbal',    'Enriched with Neem and Tulsi extracts, scientifically tested to eliminate 99.9% of harmful germs.'),
(12, 'Antiseptic Disinfectant 500ml',   6, 175.0, 4.6,  91,  15, 0, 'LifeGuard Care',   'First-aid antiseptic liquid for wound cleansing, surface disinfection, and personal hygiene.');

-- 6.6 Stock Batches (1-to-1 Sorted Alignment with Medicines 1 to 12)
-- Batch codes formatted consistently as BTC-2026-001 through BTC-2026-012
INSERT INTO stock_batches (id, medicine_id, batch_no, quantity, expiry_date, status, received_date, supplier_id) VALUES
(1,   1, 'BTC-2026-001', 240, '2027-11-15', 'ok',       '2026-08-01', 1),
(2,   2, 'BTC-2026-002', 180, '2027-10-20', 'ok',       '2026-08-01', 1),
(3,   3, 'BTC-2026-003',  60, '2026-11-10', 'low',      '2026-08-05', 1),
(4,   4, 'BTC-2026-004',   0, '2026-09-25', 'out',      '2026-08-05', 1),
(5,   5, 'BTC-2026-005', 150, '2027-04-18', 'ok',       '2026-08-10', 2),
(6,   6, 'BTC-2026-006',  75, '2027-06-30', 'ok',       '2026-08-10', 2),
(7,   7, 'BTC-2026-007',  90, '2027-08-15', 'ok',       '2026-08-12', 3),
(8,   8, 'BTC-2026-008', 120, '2027-09-20', 'ok',       '2026-08-12', 3),
(9,   9, 'BTC-2026-009',  40, '2026-10-15', 'low',      '2026-08-15', 3),
(10, 10, 'BTC-2026-010',  55, '2027-05-30', 'ok',       '2026-08-15', 3),
(11, 11, 'BTC-2026-011', 200, '2028-01-10', 'ok',       '2026-08-18', 2),
(12, 12, 'BTC-2026-012',  15, '2026-09-18', 'expiring', '2026-08-18', 2);

-- 6.7 Orders (Chronologically Sorted ORD-2026-001 to ORD-2026-005)
INSERT INTO orders (id, user_email, date, total, status, delivery_name, delivery_address, delivery_phone, time_slot, payment_method, created_at) VALUES
('ORD-2026-001', 'john@example.com',  '2026-08-15', 270.0, 'Delivered', 'John Doe',     '44, Lotus Residency, MG Road, Kochi', '+91 98765 43210', 'Morning (9 AM - 12 PM)',  'UPI / Online',    '2026-08-15 10:30:00'),
('ORD-2026-002', 'john@example.com',  '2026-08-22', 315.0, 'Delivered', 'John Doe',     '44, Lotus Residency, MG Road, Kochi', '+91 98765 43210', 'Evening (4 PM - 8 PM)',   'Card',            '2026-08-22 16:45:00'),
('ORD-2026-003', 'priya@example.com', '2026-08-29', 205.0, 'Shipped',   'Priya Sharma', '12B, Marine Drive Towers, Ernakulam', '+91 98412 34567', 'Afternoon (1 PM - 4 PM)', 'Cash on Delivery','2026-08-29 14:15:00'),
('ORD-2026-004', 'priya@example.com', '2026-09-02', 350.0, 'Confirmed', 'Priya Sharma', '12B, Marine Drive Towers, Ernakulam', '+91 98412 34567', 'Morning (9 AM - 12 PM)',  'UPI / Online',    '2026-09-02 11:20:00'),
('ORD-2026-005', 'john@example.com',  '2026-09-06', 240.0, 'Placed',    'John Doe',     '44, Lotus Residency, MG Road, Kochi', '+91 98765 43210', 'Evening (4 PM - 8 PM)',   'Cash on Delivery','2026-09-06 18:00:00');

-- 6.8 Order Items (Sorted by order_id and line item)
INSERT INTO order_items (id, order_id, medicine_id, quantity, unit_price) VALUES
-- ORD-2026-001 (Total = 90 + 180 = 270)
(1, 'ORD-2026-001',  1, 2,  45.0),
(2, 'ORD-2026-001',  5, 1, 180.0),
-- ORD-2026-002 (Total = 95 + 220 = 315)
(3, 'ORD-2026-002', 11, 1,  95.0),
(4, 'ORD-2026-002',  6, 1, 220.0),
-- ORD-2026-003 (Total = 160 + 45 = 205)
(5, 'ORD-2026-003',  9, 1, 160.0),
(6, 'ORD-2026-003',  1, 1,  45.0),
-- ORD-2026-004 (Total = 210 + 140 = 350)
(7, 'ORD-2026-004',  7, 1, 210.0),
(8, 'ORD-2026-004', 10, 1, 140.0),
-- ORD-2026-005 (Total = 240)
(9, 'ORD-2026-005',  3, 2, 120.0);

-- 6.9 Prescriptions (Sorted by Date)
INSERT INTO prescriptions (id, filename, patient_name, doctor_name, date, status, order_id, user_email, notes, created_at) VALUES
(1, 'rx_amoxicillin_john.pdf', 'John Doe',   'Dr. Kavya Suresh', '2026-08-20', 'Verified', 'ORD-2026-001', 'john@example.com',  'Prescription verified for Amoxicillin course.', '2026-08-20 11:00:00'),
(2, 'rx_pediatric_colic.pdf',  'Baby Maya',  'Dr. Paul Mathew',  '2026-08-28', 'Verified', 'ORD-2026-003', 'priya@example.com', 'Pediatric colic drops prescription approved.', '2026-08-28 15:30:00'),
(3, 'rx_respiratory_care.pdf', 'Priya Sharma','Dr. Kavya Suresh', '2026-09-05', 'Pending',  '',             'priya@example.com', 'Under review for antibiotic refill.',           '2026-09-05 16:20:00');

-- 6.10 Audit Log Initial Entries
INSERT INTO audit_log (action, entity, entity_id, user_email, user_type, timestamp, details) VALUES
('SYSTEM_INIT', 'database', '0', 'system', 'system', '2026-08-01 00:00:00', 'Initialized 10-table normalized 3NF schema with 6 views, 5 triggers, 10 indexes.');

