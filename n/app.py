import http.server
import socketserver
import json
import sqlite3
import urllib.parse
import os
import sys
import webbrowser

DB_FILE = os.path.join(os.path.dirname(__file__), "pharmacy.db")
PORT = 8000

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        key TEXT PRIMARY KEY,
        name TEXT,
        icon TEXT
    )""")

    # Check if manufacturer column exists in medicines, if not recreate or alter
    cursor.execute("PRAGMA table_info(medicines)")
    columns = [row[1] for row in cursor.fetchall()]
    if columns and 'manufacturer' not in columns:
        cursor.execute("DROP TABLE medicines")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        cat TEXT,
        manufacturer TEXT,
        price REAL,
        rating REAL,
        reviews INTEGER,
        stock INTEGER,
        rx INTEGER,
        desc TEXT,
        uses TEXT,
        dosage TEXT,
        composition TEXT,
        side_effects TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS suppliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        contact TEXT,
        phone TEXT,
        email TEXT,
        cats TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id TEXT PRIMARY KEY,
        date TEXT,
        total REAL,
        status TEXT,
        address TEXT,
        payment_method TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        medicine_id INTEGER,
        qty INTEGER,
        price REAL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS prescriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file TEXT,
        patient TEXT,
        doctor TEXT,
        date TEXT,
        status TEXT,
        order_id TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medicine_id INTEGER,
        name TEXT,
        rating INTEGER,
        text TEXT,
        date TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT,
        address TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        batch TEXT,
        stock INTEGER,
        expiry TEXT,
        status TEXT
    )""")

    # Seed data if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        categories = [
            ('pain', 'Pain Relief', 'M10 14a4 4 0 0 1 0-5.7l3-3a4 4 0 1 1 5.7 5.7l-1.5 1.5 M14 10a4 4 0 0 1 0 5.7l-3 3a4 4 0 1 1-5.7-5.7l1.5-1.5'),
            ('antibiotics', 'Antibiotics', 'M12 2l8 4v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4z'),
            ('vitamins', 'Vitamins', 'M12 21c-4-2-7-6-7-11a7 7 0 0 1 14 0c0 5-3 9-7 11z'),
            ('skincare', 'Skin Care', 'M12 3c3 3.5 6 7 6 10.5A6 6 0 0 1 6 13.5C6 10 9 6.5 12 3z'),
            ('babycare', 'Baby Care', 'M7 9h10v6a5 5 0 0 1-10 0V9zM9 9V7a3 3 0 0 1 6 0v2'),
            ('personalcare', 'Personal Care', 'M20.8 4.6a5 5 0 0 0-7.1 0L12 6.3l-1.7-1.7a5 5 0 1 0-7.1 7.1L12 20.4l8.8-8.7a5 5 0 0 0 0-7.1z')
        ]
        cursor.executemany("INSERT INTO categories VALUES (?,?,?)", categories)

    cursor.execute("SELECT COUNT(*) FROM medicines")
    if cursor.fetchone()[0] == 0:
        medicines = [
            (1, 'Paracetamol 500mg', 'pain', 'Cipla Health', 45.0, 4.8, 120, 240, 0,
             'Relieves mild to moderate pain and reduces fever. Adults: one tablet every 4–6 hours, not exceeding 8 tablets in 24 hours.',
             'Headache, Toothache, Muscle pain, Fever reduction',
             '1 tablet every 4 to 6 hours as needed. Do not exceed 4000mg per day.',
             'Paracetamol / Acetaminophen 500mg, Binding excipients',
             'Rare: Nausea, allergic skin rash. Consult doctor if symptoms persist past 3 days.'),

            (2, 'Amoxicillin 250mg', 'antibiotics', 'Sun Pharmaceutical', 120.0, 4.6, 88, 60, 1,
             'Broad-spectrum penicillin antibiotic used for treating bacterial infections. Complete full prescribed course.',
             'Respiratory tract infections, ENT bacterial infections, Skin infections',
             'Take 1 capsule 3 times daily after meals for 5–7 days as directed by physician.',
             'Amoxicillin Trihydrate equivalent to 250mg anhydrous amoxicillin',
             'Mild diarrhea, nausea, stomach upset. Discontinue and notify doctor if rash occurs.'),

            (3, 'Vitamin C 1000mg', 'vitamins', 'Abbott Healthcare', 180.0, 4.7, 210, 150, 0,
             'High-potency effervescent Vitamin C with Zinc for immunity support and antioxidant protection.',
             'Immune system boost, Collagen synthesis, Cold symptom relief',
             'Dissolve 1 effervescent tablet daily in a 200ml glass of cold drinking water.',
             'Ascorbic Acid (Vitamin C) 1000mg, Zinc Sulfate 10mg, Orange Flavor',
             'Mild gastric upset if taken on an empty stomach.'),

            (4, 'Soothing Aloe Gel', 'skincare', 'Himalaya Wellness', 210.0, 4.5, 64, 90, 0,
             'Pure organic aloe vera extract gel for soothing skin irritation, sunburns, and hydration.',
             'Sunburn relief, Skin hydration, Minor burns & redness',
             'Apply gently onto clean affected skin areas 2–3 times daily.',
             'Organic Aloe Barbadensis Leaf Juice 99%, Vitamin E, Cucumber Extract',
             'Hypoallergenic; test patch recommended for hyper-sensitive skin.'),

            (5, 'Baby Colic Drops', 'babycare', 'Mankind Pharma', 160.0, 4.4, 52, 40, 0,
             'Paediatric oral drops providing fast relief from infant gas, colic pain and abdominal discomfort.',
             'Infant gas relief, Colic abdominal pain, Bloating',
             'Infants (under 6 months): 5–10 drops before feeds, max 4 times daily.',
             'Simethicone 40mg, Dill Oil 0.005ml, Fennel Oil 0.0007ml',
             'Safe for infants when used as directed by pediatrician.'),

            (6, 'Herbal Hand Wash', 'personalcare', 'Dabur India', 95.0, 4.3, 73, 200, 0,
             'Antibacterial liquid hand wash infused with natural neem and tulsi extracts for 99.9% germ protection.',
             'Hand hygiene, Antibacterial cleansing, Skin moisture retention',
             'Pump a small quantity onto wet hands, lather well for 20 seconds, and rinse.',
             'Neem Leaf Extract, Tulsi Oil, Glycerin, Cleansing agents',
             'For external hand hygiene only. Avoid contact with eyes.'),

            (7, 'Ibuprofen 400mg', 'pain', 'Dr. Reddys Labs', 60.0, 4.6, 98, 12, 0,
             'Fast-acting NSAID tablet for relieving acute body pain, dental pain, and joint inflammation.',
             'Arthritis pain, Dysmenorrhea, Migraine, Post-op swelling',
             '1 tablet twice daily after food. Take with milk or water.',
             'Ibuprofen IP 400mg',
             'Heartburn, mild stomach discomfort. Take always after meals.'),

            (8, 'Azithromycin 500mg', 'antibiotics', 'Zydus Cadila', 150.0, 4.5, 41, 0, 1,
             'Macrolide antibiotic prescribed for bacterial chest infections, tonsillitis, and typhoid fever.',
             'Community acquired pneumonia, Sinusitis, Skin bacterial infections',
             '1 tablet once daily 1 hour before or 2 hours after food for 3 days.',
             'Azithromycin Dihydrate equivalent to 500mg Azithromycin',
             'Abdominal cramps, loose stools. Complete full duration prescribed.'),

            (9, 'Multivitamin Gummies', 'vitamins', 'HealthKart', 220.0, 4.8, 134, 75, 0,
             'Tasty chewable multivitamin gummies packed with Vitamin A, B-Complex, C, D3, E and Minerals.',
             'Daily nutrition fill, Energy support, Eye & Bone health',
             'Adults: Chew 2 gummies daily. No water needed.',
             'Vitamin A, B6, B12, C, D3, E, Biotin, Zinc, Folic Acid',
             'Do not exceed recommended daily dose.'),

            (10, 'Baby Diaper Rash Cream', 'babycare', 'Sebamed Baby', 140.0, 4.6, 59, 55, 0,
             'Dermatologically tested barrier cream with 15% Zinc Oxide and Panthenol for protecting baby skin.',
             'Diaper rash treatment, Moisture barrier protection, Chapped skin',
             'Apply liberally to clean dry diaper area during every diaper change.',
             'Micronized Zinc Oxide 15%, Panthenol (Pro-Vitamin B5), Chamomile',
             'Non-irritating, pH 5.5 balanced formula.')
        ]
        cursor.executemany("INSERT INTO medicines VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", medicines)

    cursor.execute("SELECT COUNT(*) FROM suppliers")
    if cursor.fetchone()[0] == 0:
        suppliers = [
            (1, 'MedSupply Co.', 'Suresh Nair', '+91 98450 11223', 'suresh@medsupply.in', 'Pain Relief, Antibiotics'),
            (2, 'Wellness Distributors', 'Priya Menon', '+91 97460 22110', 'priya@wellnessdist.in', 'Vitamins, Personal Care'),
            (3, 'BabyCare Traders', 'Arun Das', '+91 94470 33987', 'arun@babycaretraders.in', 'Baby Care, Skin Care')
        ]
        cursor.executemany("INSERT INTO suppliers VALUES (?,?,?,?,?,?)", suppliers)

    cursor.execute("SELECT COUNT(*) FROM orders")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO orders VALUES ('ORD-1042', '2026-08-20', 270.0, 'Delivered', '44, Lotus Residency, MG Road, Kochi, Kerala 682016', 'card')")
        cursor.execute("INSERT INTO order_items (order_id, medicine_id, qty, price) VALUES ('ORD-1042', 1, 2, 45.0)")
        cursor.execute("INSERT INTO order_items (order_id, medicine_id, qty, price) VALUES ('ORD-1042', 3, 1, 180.0)")

        cursor.execute("INSERT INTO orders VALUES ('ORD-1088', '2026-08-27', 315.0, 'Shipped', '44, Lotus Residency, MG Road, Kochi, Kerala 682016', 'upi')")
        cursor.execute("INSERT INTO order_items (order_id, medicine_id, qty, price) VALUES ('ORD-1088', 6, 1, 95.0)")
        cursor.execute("INSERT INTO order_items (order_id, medicine_id, qty, price) VALUES ('ORD-1088', 9, 1, 220.0)")

    cursor.execute("SELECT COUNT(*) FROM prescriptions")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO prescriptions VALUES (1, 'prescription_aug.pdf', 'John Doe', 'Dr. Kavya Suresh', '2026-08-25', 'Verified', 'ORD-1042')")

    cursor.execute("SELECT COUNT(*) FROM reviews")
    if cursor.fetchone()[0] == 0:
        reviews = [
            (1, 'Anjali R.', 5, 'Worked well and delivery was quick. Packaging was neat too.', '2026-08-15'),
            (1, 'Rahul K.', 5, 'Good value for the price, will order again.', '2026-08-18'),
            (2, 'Priya M.', 4, 'Exactly as described. No issues with quality.', '2026-08-20'),
            (2, 'Suresh N.', 5, 'Fast verification for my prescription, smooth checkout.', '2026-08-22')
        ]
        cursor.executemany("INSERT INTO reviews (medicine_id, name, rating, text, date) VALUES (?,?,?,?,?)", reviews)

    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user_profile VALUES (1, 'John Doe', 'john@example.com', '+91 98765 43210', '44, Lotus Residency, MG Road, Kochi, Kerala 682016')")

    cursor.execute("SELECT COUNT(*) FROM admin_stock")
    if cursor.fetchone()[0] == 0:
        admin_stock = [
            ('Paracetamol 500mg', 'B1042', 240, '2026-11-15', 'ok'),
            ('Amoxicillin 250mg', 'B2210', 60, '2026-09-20', 'low'),
            ('Ibuprofen 400mg', 'B3305', 12, '2026-09-05', 'expiring'),
            ('Azithromycin 500mg', 'B4471', 0, '2026-10-02', 'out'),
            ('Vitamin C 1000mg', 'B5120', 150, '2027-02-18', 'ok'),
            ('Multivitamin Gummies', 'B5522', 75, '2026-12-01', 'ok')
        ]
        cursor.executemany("INSERT INTO admin_stock (name, batch, stock, expiry, status) VALUES (?,?,?,?,?)", admin_stock)

    conn.commit()
    conn.close()


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MediCart Pharmacy — Wireframe Exact Match (Python & SQLite)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --green-900:#0B3B2E;
  --green-700:#0E8A5A;
  --green-600:#129966;
  --green-50:#EAF6F0;
  --ink:#16241C;
  --ink-muted:#5B6B63;
  --paper:#FFFFFF;
  --line:#DCE6E0;
  --amber:#C97A2B;
  --red:#B84A3E;
  --radius:12px;
}
*{box-sizing:border-box;}
html,body{margin:0;padding:0;max-width:100%;overflow-x:hidden;}
body{
  font-family:'Inter',sans-serif;
  color:var(--ink);
  background:var(--paper);
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif;margin:0;color:var(--ink);}
p{margin:0;}
a{color:inherit;text-decoration:none;}
button{font-family:inherit;cursor:pointer;}
input,select,textarea{font-family:inherit;font-size:14px;}
:focus-visible{outline:2px solid var(--green-700);outline-offset:2px;}
img,svg{display:block;}

.page{display:none;}
.page.active{display:block;animation:fade .25s ease;}
@keyframes fade{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:translateY(0);}}

/* ---------- shared elements ---------- */
.section-pad{padding:40px 6vw;}
.btn{
  display:inline-flex;align-items:center;justify-content:center;gap:8px;
  border-radius:8px;padding:12px 22px;font-weight:600;font-size:14px;
  border:1px solid transparent;transition:transform .1s ease, background .15s ease, border-color .15s ease;
}
.btn:active{transform:scale(.98);}
.btn-primary{background:var(--green-700);color:#fff;}
.btn-primary:hover{background:var(--green-600);}
.btn-outline{background:transparent;border-color:var(--green-700);color:var(--green-700);}
.btn-outline:hover{background:var(--green-50);}
.btn-ghost{background:transparent;color:var(--ink-muted);border-color:var(--line);}
.btn-ghost:hover{border-color:var(--green-700);color:var(--green-700);}
.btn-danger{background:transparent;color:var(--red);border-color:var(--red);}
.btn-danger:hover{background:#FBEDEA;}
.btn-sm{padding:7px 14px;font-size:13px;}
.btn-block{width:100%;}
.field{display:flex;flex-direction:column;gap:6px;margin-bottom:16px;}
.field label{font-size:13px;font-weight:600;color:var(--ink-muted);}
.field input,.field select,.field textarea{
  border:1px solid var(--line);border-radius:8px;padding:11px 12px;background:#fff;color:var(--ink);
}
.field input:focus,.field select:focus,.field textarea:focus{border-color:var(--green-700);}
.card{border:1px solid var(--line);border-radius:var(--radius);padding:22px;background:#fff;}
.muted{color:var(--ink-muted);}
.small{font-size:13px;}
.divider{height:1px;background:var(--line);margin:28px 0;}
.badge{display:inline-flex;align-items:center;font-size:12px;font-weight:600;padding:3px 9px;border-radius:999px;}
.badge-green{background:var(--green-50);color:var(--green-700);}
.badge-amber{background:#FCF1E4;color:var(--amber);}
.badge-red{background:#FBEDEA;color:var(--red);}
.badge-grey{background:#F1F3F1;color:var(--ink-muted);}
.icon{width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;}
table{width:100%;border-collapse:collapse;}
th{text-align:left;font-size:12px;text-transform:none;color:var(--ink-muted);font-weight:600;padding:10px 12px;border-bottom:1px solid var(--line);}
td{padding:12px;border-bottom:1px solid var(--line);font-size:14px;}
tr:last-child td{border-bottom:none;}

/* ---------- nav ---------- */
.nav{
  display:flex;align-items:center;justify-content:space-between;gap:24px;
  padding:14px 6vw;border-bottom:1px solid var(--line);position:sticky;top:0;background:#fff;z-index:80;
}
.brand{display:flex;align-items:center;gap:10px;font-family:'Space Grotesk';font-weight:700;font-size:19px;white-space:nowrap;}
.brand-mark{width:32px;height:32px;border-radius:9px;background:var(--green-700);display:flex;align-items:center;justify-content:center;}
.brand-mark svg{width:18px;height:18px;stroke:#fff;fill:none;stroke-width:2;}
.nav__links{display:flex;gap:26px;flex-wrap:wrap;}
.nav__links a{font-size:14px;font-weight:500;color:var(--ink-muted);padding:6px 0;border-bottom:2px solid transparent;cursor:pointer;}
.nav__links a.active,.nav__links a:hover{color:var(--green-700);border-color:var(--green-700);}
.nav__right{display:flex;align-items:center;gap:14px;}
.search-box{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:8px;padding:8px 12px;min-width:190px;}
.search-box input{border:none;outline:none;flex:1;font-size:13px;}
.icon-btn{position:relative;width:38px;height:38px;border-radius:8px;border:1px solid var(--line);background:#fff;display:flex;align-items:center;justify-content:center;}
.icon-btn:hover{border-color:var(--green-700);}
.cart-count{position:absolute;top:-6px;right:-6px;background:var(--red);color:#fff;font-size:10px;font-weight:700;min-width:16px;height:16px;border-radius:999px;display:flex;align-items:center;justify-content:center;padding:0 3px;}

/* ---------- hero ---------- */
.hero{display:grid;grid-template-columns:1.05fr .95fr;gap:48px;padding:64px 6vw;background:var(--green-50);align-items:center;}
.hero h1{font-size:clamp(2rem,3.6vw,3.1rem);line-height:1.08;letter-spacing:-.01em;}
.hero h1 span{color:var(--green-700);}
.hero p{margin-top:16px;color:var(--ink-muted);font-size:15.5px;max-width:44ch;}
.hero .btn{margin-top:24px;}
.hero-art{width:100%;height:auto;}

.trust-row{display:flex;gap:0;padding:26px 6vw;border-bottom:1px solid var(--line);flex-wrap:wrap;}
.trust-item{flex:1;min-width:180px;display:flex;gap:12px;align-items:flex-start;padding:0 20px;border-left:1px solid var(--line);}
.trust-item:first-child{border-left:none;padding-left:0;}
.trust-item svg{width:22px;height:22px;stroke:var(--green-700);fill:none;stroke-width:1.6;flex-shrink:0;margin-top:2px;}
.trust-item h4{font-size:14.5px;}
.trust-item p{font-size:12.5px;color:var(--ink-muted);margin-top:2px;}

.stats-row{display:flex;padding:34px 6vw;flex-wrap:wrap;}
.stat{flex:1;min-width:150px;padding:0 20px;border-left:1px solid var(--line);}
.stat:first-child{border-left:none;padding-left:0;}
.stat b{display:block;font-family:'Space Grotesk';font-size:28px;color:var(--green-700);}
.stat span{font-size:12.5px;color:var(--ink-muted);}

.browse-head{display:flex;align-items:baseline;justify-content:space-between;padding:8px 6vw 20px;}
.browse-head a{font-size:13.5px;font-weight:600;color:var(--green-700);}
.cat-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;padding:0 6vw 56px;}
.cat-chip{border:1px solid var(--line);border-radius:var(--radius);padding:20px 10px;text-align:center;background:none;cursor:pointer;}
.cat-chip svg{width:26px;height:26px;stroke:var(--green-700);fill:none;stroke-width:1.6;margin:0 auto 10px;}
.cat-chip:hover{border-color:var(--green-700);background:var(--green-50);}
.cat-chip b{display:block;font-size:13px;}
.cat-chip span{font-size:11.5px;color:var(--ink-muted);}

.footer{background:var(--green-900);color:#DCEFE5;padding:52px 6vw 22px;}
.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:36px;}
.footer h4{color:#fff;font-size:14px;margin-bottom:14px;}
.footer p,.footer a{font-size:13px;color:#AFCABE;display:block;margin-bottom:8px;}
.footer a:hover{color:#fff;}
.footer-bottom{display:flex;justify-content:space-between;margin-top:36px;padding-top:20px;border-top:1px solid rgba(255,255,255,.12);font-size:12.5px;color:#8EAE9F;flex-wrap:wrap;gap:8px;}
.footer-bottom a{color:#8EAE9F;}
.footer-bottom a:hover{color:#fff;}

/* ---------- breadcrumb ---------- */
.crumb-bar{padding:18px 6vw 0;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;}
.crumb{font-size:13px;color:var(--ink-muted);}
.crumb b{color:var(--ink);font-weight:600;}

/* ---------- medicines page ---------- */
.med-layout{display:grid;grid-template-columns:250px 1fr;gap:30px;padding:24px 6vw 60px;align-items:start;}
.filters h4{font-size:13px;text-transform:uppercase;letter-spacing:.03em;color:var(--ink-muted);margin-bottom:14px;}
.filter-group{margin-bottom:20px;}
.filter-group .fg-title{font-size:13.5px;font-weight:600;margin-bottom:8px;}
.chip-list label{display:flex;align-items:center;gap:8px;font-size:13.5px;padding:5px 0;color:var(--ink-muted);}
.chip-list input{accent-color:var(--green-700);}
.med-toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;flex-wrap:wrap;gap:10px;}
.med-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:18px;}
.med-card{border:1px solid var(--line);border-radius:var(--radius);padding:16px;display:flex;flex-direction:column;gap:8px;background:#fff;text-align:left;cursor:pointer;}
.med-card:hover{border-color:var(--green-700);box-shadow:0 4px 16px rgba(14,138,90,.10);}
.med-thumb{width:100%;height:100px;border-radius:8px;background:var(--green-50);display:flex;align-items:center;justify-content:center;}
.med-thumb svg{width:34px;height:34px;stroke:var(--green-700);fill:none;stroke-width:1.5;}
.med-card h4{font-size:14.5px;}
.med-mfg{font-size:12px;color:var(--ink-muted);}
.med-rating{font-size:12.5px;color:var(--amber);}
.med-rating span{color:var(--ink-muted);}
.med-price-row{display:flex;justify-content:space-between;align-items:center;margin-top:auto;}
.med-price{font-family:'Space Grotesk';font-weight:700;font-size:16px;}

.pagination-bar{display:flex;align-items:center;justify-content:center;gap:12px;margin-top:32px;}
.pagination-bar button{padding:6px 14px;border:1px solid var(--line);border-radius:6px;background:#fff;font-size:13px;}
.pagination-bar button:disabled{opacity:0.4;cursor:not-allowed;}

/* ---------- detail page ---------- */
.detail-layout{display:grid;grid-template-columns:300px 1fr 280px;gap:26px;padding:24px 6vw 10px;align-items:start;}
.detail-img{width:100%;aspect-ratio:1;border-radius:var(--radius);background:var(--green-50);display:flex;align-items:center;justify-content:center;}
.detail-img svg{width:70px;height:70px;stroke:var(--green-700);fill:none;stroke-width:1.3;}
.detail-info h2{font-size:22px;margin-bottom:2px;}
.detail-info .mfg-line{font-size:13px;color:var(--ink-muted);margin-bottom:8px;}
.detail-info .rating-line{display:flex;align-items:center;gap:8px;margin:10px 0;font-size:13.5px;}
.detail-price{font-family:'Space Grotesk';font-size:24px;font-weight:700;margin:14px 0 6px;}
.qty-row{display:flex;align-items:center;gap:10px;margin-bottom:14px;}
.qty-btn{width:32px;height:32px;border:1px solid var(--line);background:#fff;border-radius:6px;font-size:16px;}
.qty-val{width:34px;text-align:center;font-weight:600;}
.tabs{display:flex;gap:26px;border-bottom:1px solid var(--line);margin:36px 6vw 0;flex-wrap:wrap;}
.tab-btn{background:none;border:none;padding:10px 2px;font-size:14px;color:var(--ink-muted);border-bottom:2px solid transparent;}
.tab-btn.active{color:var(--green-700);font-weight:600;border-color:var(--green-700);}
.tab-panel{display:none;padding:24px 6vw 10px;}
.tab-panel.active{display:block;}
.review{border:1px solid var(--line);border-radius:var(--radius);padding:16px;margin-bottom:12px;}
.review-head{display:flex;justify-content:space-between;font-size:13.5px;font-weight:600;margin-bottom:6px;}
.related-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px;padding:24px 6vw 56px;}

/* ---------- generic two-col layout ---------- */
.two-col{display:grid;grid-template-columns:1.4fr 1fr;gap:26px;padding:28px 6vw 56px;align-items:start;}
.two-col.reverse{grid-template-columns:1fr 1.4fr;}
.summary-line{display:flex;justify-content:space-between;padding:9px 0;font-size:14px;color:var(--ink-muted);}
.summary-line.total{color:var(--ink);font-weight:700;font-size:16px;border-top:1px solid var(--line);margin-top:6px;padding-top:14px;}
.pay-options{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:14px 0 20px;}
.pay-opt{border:1px solid var(--line);border-radius:8px;padding:12px;text-align:center;font-size:13px;font-weight:600;background:#fff;}
.pay-opt.selected{border-color:var(--green-700);background:var(--green-50);color:var(--green-700);}

/* ---------- order tracker ---------- */
.tracker{display:flex;align-items:flex-start;padding:20px 4px;}
.step{flex:1;text-align:center;position:relative;}
.step .dot{width:22px;height:22px;border-radius:50%;border:2px solid var(--line);background:#fff;margin:0 auto 8px;display:flex;align-items:center;justify-content:center;}
.step .line{position:absolute;top:11px;left:-50%;width:100%;height:2px;background:var(--line);z-index:-1;}
.step:first-child .line{display:none;}
.step.done .dot{background:var(--green-700);border-color:var(--green-700);}
.step.done .line{background:var(--green-700);}
.step span{font-size:12px;color:var(--ink-muted);}
.step.done span{color:var(--ink);font-weight:600;}

/* ---------- upload box ---------- */
.upload-box{border:1.5px dashed var(--line);border-radius:var(--radius);padding:34px;text-align:center;color:var(--ink-muted);font-size:13.5px;margin-bottom:18px;cursor:pointer;}
.upload-box svg{width:26px;height:26px;stroke:var(--green-700);fill:none;stroke-width:1.5;margin:0 auto 10px;}
.upload-box b{color:var(--green-700);}

/* ---------- profile ---------- */
.profile-head{display:flex;gap:18px;align-items:center;}
.avatar{width:60px;height:60px;border-radius:50%;background:var(--green-700);color:#fff;display:flex;align-items:center;justify-content:center;font-family:'Space Grotesk';font-weight:700;font-size:20px;}
.rx-doc{border:1px solid var(--line);border-radius:var(--radius);padding:14px;display:flex;align-items:center;gap:10px;font-size:13px;}
.rx-doc svg{width:20px;height:20px;stroke:var(--green-700);fill:none;stroke-width:1.6;flex-shrink:0;}
.rx-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px;margin-top:14px;}

/* ---------- admin ---------- */
.admin-nav{background:var(--green-900);color:#fff;}
.admin-nav .brand{color:#fff;}
.admin-nav .nav__links a{color:#AFCABE;}
.admin-nav .nav__links a.active,.admin-nav .nav__links a:hover{color:#fff;border-color:#fff;}
.admin-nav .btn-outline{border-color:#AFCABE;color:#fff;}
.kpi-row{display:flex;gap:18px;padding:28px 6vw 8px;flex-wrap:wrap;}
.kpi{flex:1;min-width:190px;border:1px solid var(--line);border-radius:var(--radius);padding:18px 20px;}
.kpi span{font-size:12.5px;color:var(--ink-muted);}
.kpi b{display:block;font-family:'Space Grotesk';font-size:24px;margin-top:6px;}
.admin-section{padding:28px 6vw;}
.chart{display:flex;align-items:flex-end;gap:12px;height:170px;padding-top:20px;border-bottom:1px solid var(--line);}
.chart .bar-wrap{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;gap:8px;}
.chart .bar{width:60%;background:var(--green-700);border-radius:5px 5px 0 0;}
.chart .bar-wrap span{font-size:11px;color:var(--ink-muted);}

/* ---------- login ---------- */
.auth-wrap{display:flex;justify-content:center;padding:60px 6vw 80px;}
.auth-card{width:100%;max-width:380px;border:1px solid var(--line);border-radius:var(--radius);padding:34px;}
.auth-tabs{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:26px;}
.auth-tabs button{flex:1;padding:10px;border:none;background:#fff;font-weight:600;font-size:13.5px;color:var(--ink-muted);}
.auth-tabs button.active{background:var(--green-700);color:#fff;}
.auth-panel{display:none;}
.auth-panel.active{display:block;}

/* ---------- toast ---------- */
#toast{position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(20px);background:var(--ink);color:#fff;padding:12px 20px;border-radius:8px;font-size:13.5px;opacity:0;pointer-events:none;transition:all .25s ease;z-index:200;}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0);}

/* ---------- misc page header ---------- */
.page-head{padding:44px 6vw 8px;}
.page-head p{color:var(--ink-muted);margin-top:8px;max-width:60ch;font-size:14.5px;}

.menu-toggle{display:none;width:38px;height:38px;border-radius:8px;border:1px solid var(--line);background:#fff;align-items:center;justify-content:center;}
@media(max-width:980px){
  .menu-toggle{display:flex;}
  .nav{padding:12px 4vw;gap:10px;}
  .brand{font-size:16px;gap:8px;}
  .nav__right{gap:8px;}
  #accountBtn{padding:9px 14px;}
  .nav__links{
    display:none;position:absolute;top:100%;left:0;right:0;background:#fff;
    flex-direction:column;gap:0;padding:8px 6vw 14px;border-bottom:1px solid var(--line);
  }
  .nav__links.open{display:flex;}
  .nav__links a{padding:12px 0;border-bottom:1px solid var(--line);}
  .hero{grid-template-columns:1fr;}
  .cat-grid{grid-template-columns:repeat(3,1fr);}
  .med-layout{grid-template-columns:1fr;}
  .detail-layout{grid-template-columns:1fr;}
  .two-col{grid-template-columns:1fr;}
  .two-col.reverse{grid-template-columns:1fr;}
  .footer-grid{grid-template-columns:1fr 1fr;}
  .search-box{display:none;}
}
</style>
</head>
<body>

<div id="toast"></div>

<!-- ================= CUSTOMER NAV ================= -->
<nav class="nav" id="customerNav">
  <a href="#" class="brand" data-page="home">
    <span class="brand-mark"><svg viewBox="0 0 24 24"><path d="M12 3v18M3 12h18"/></svg></span>
    MediCart Pharmacy
  </a>
  <div class="nav__links" id="navLinks">
    <a data-page="home">Home</a>
    <a data-page="medicines">Medicines</a>
    <a data-page="prescriptions">Prescriptions</a>
    <a data-page="orders">Orders</a>
    <a data-page="profile">Profile</a>
    <a data-page="about">About Us</a>
    <a data-page="contact">Contact</a>
  </div>
  <div class="nav__right" id="navRight">
    <div class="search-box">
      <svg class="icon" style="width:16px;height:16px;stroke:var(--ink-muted)" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
      <input id="searchInput" placeholder="Search medicines...">
    </div>
    <button class="icon-btn" data-page="cart" aria-label="Cart">
      <svg class="icon" viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M1 1h4l2.6 13.4a2 2 0 0 0 2 1.6h9.4a2 2 0 0 0 2-1.6L23 6H6"/></svg>
      <span class="cart-count" id="cartCount">0</span>
    </button>
    <button class="btn btn-outline btn-sm" id="accountBtn" data-page="login">Login</button>
    <button class="menu-toggle" id="menuToggle" aria-label="Menu">
      <svg class="icon" style="stroke:var(--ink)" viewBox="0 0 24 24"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
    </button>
  </div>
</nav>

<!-- ================= ADMIN NAV ================= -->
<nav class="nav admin-nav" id="adminNav" style="display:none;">
  <a href="#" class="brand" data-page="admin">
    <span class="brand-mark" style="background:#fff;"><svg viewBox="0 0 24 24" style="stroke:var(--green-900)"><path d="M12 3v18M3 12h18"/></svg></span>
    Admin Panel
  </a>
  <div class="nav__links">
    <a data-page="admin">Dashboard</a>
    <a data-page="admin">Inventory &amp; Expiry</a>
    <a data-page="suppliers">Suppliers</a>
    <a data-page="admin">Sales Reports</a>
    <a data-page="orders">Orders</a>
  </div>
  <div class="nav__right">
    <button class="btn btn-outline btn-sm" data-page="home">Exit to Storefront</button>
  </div>
</nav>

<main>

<!-- ================= 1. HOME ================= -->
<section class="page active" id="page-home">
  <div class="hero">
    <div>
      <h1>Your health,<br><span>our priority.</span></h1>
      <p>Order genuine medicines online, upload prescriptions in seconds, and get everything delivered straight to your door.</p>
      <button class="btn btn-primary" data-page="medicines">Order Now →</button>
    </div>
    <svg class="hero-art" viewBox="0 0 360 300" fill="none" stroke="#0E8A5A" stroke-width="1.4">
      <rect x="110" y="60" width="140" height="190" rx="14"/>
      <line x1="110" y1="108" x2="250" y2="108"/>
      <rect x="150" y="30" width="60" height="34" rx="6"/>
      <circle cx="160" cy="150" r="12"/><circle cx="200" cy="150" r="12"/><circle cx="180" cy="180" r="12"/>
      <path d="M40 250 h60 M60 230 v40" stroke-width="3"/>
      <path d="M280 90 h50 M305 65 v50" stroke-width="3"/>
      <circle cx="60" cy="90" r="18"/>
      <circle cx="310" cy="220" r="16"/>
    </svg>
  </div>

  <div class="trust-row">
    <div class="trust-item">
      <svg viewBox="0 0 24 24"><path d="M12 2l8 4v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4z"/></svg>
      <div><h4>Genuine Medicines</h4><p>100% original products</p></div>
    </div>
    <div class="trust-item">
      <svg viewBox="0 0 24 24"><path d="M3 12h13l4 4M3 12l4-4M3 12v6h3"/><rect x="16" y="9" width="5" height="7"/></svg>
      <div><h4>Fast Delivery</h4><p>On-time at your door</p></div>
    </div>
    <div class="trust-item">
      <svg viewBox="0 0 24 24"><path d="M12 21s7-4.4 7-11V5l-7-3-7 3v5c0 6.6 7 11 7 11z"/></svg>
      <div><h4>Secure &amp; Safe</h4><p>Your health, our priority</p></div>
    </div>
  </div>

  <div class="stats-row">
    <div class="stat"><b id="statMedCount">3,500+</b><span>Medicines Available</span></div>
    <div class="stat"><b id="statRxCount">1,200+</b><span>Prescriptions Processed</span></div>
    <div class="stat"><b id="statOrderCount">950+</b><span>Orders Delivered</span></div>
    <div class="stat"><b>2,500+</b><span>Happy Customers</span></div>
  </div>

  <div class="browse-head">
    <h2 style="font-size:22px;">Browse Medicines</h2>
    <a href="#" data-page="medicines">View All →</a>
  </div>
  <div class="cat-grid" id="homeCatGrid"></div>

  <div class="trust-row" style="border-top:1px solid var(--line);border-bottom:none;background:var(--green-50);">
    <div class="trust-item"><svg viewBox="0 0 24 24"><path d="M12 3v12M7 8l5-5 5 5"/><path d="M4 21h16"/></svg><div><h4>Upload Prescription</h4><p>Upload and get medicines</p></div></div>
    <div class="trust-item"><svg viewBox="0 0 24 24"><path d="M12 2l8 4v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4z"/><path d="M9 12l2 2 4-4"/></svg><div><h4>Secure Payment</h4><p>100% secure transactions</p></div></div>
    <div class="trust-item"><svg viewBox="0 0 24 24"><path d="M9 14L4 9l5-5M4 9h11a5 5 0 0 1 0 10h-1"/></svg><div><h4>Easy Returns</h4><p>Hassle-free returns</p></div></div>
    <div class="trust-item"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9 10a3 3 0 0 1 6 0c0 2-3 2-3 5"/><circle cx="12" cy="18" r=".5"/></svg><div><h4>24/7 Support</h4><p>We are here to help</p></div></div>
  </div>

  <div class="footerContainer"></div>
</section>

<!-- ================= 2. MEDICINES ================= -->
<section class="page" id="page-medicines">
  <div class="crumb-bar">
    <div class="crumb"><a data-page="home">Home</a> <b>&gt; Medicines</b></div>
    <div class="search-box" style="min-width:260px;">
      <svg class="icon" style="width:16px;height:16px;stroke:var(--ink-muted)" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>
      <input id="catSearchInput" placeholder="Search medicines in catalogue...">
    </div>
  </div>
  <div class="med-layout">
    <aside class="filters card">
      <h4>Filter Sidebar</h4>
      <div class="filter-group">
        <div class="fg-title">Category</div>
        <div class="chip-list" id="filterCategories"></div>
      </div>
      <div class="filter-group">
        <div class="fg-title">Max Price: ₹<span id="priceVal">300</span></div>
        <input type="range" id="priceRange" min="40" max="300" value="300" style="width:100%;accent-color:var(--green-700);">
      </div>
      <div class="filter-group">
        <label class="small" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="ratingFilter" style="accent-color:var(--green-700);"> 4★ &amp; above only</label>
      </div>
      <div class="filter-group">
        <label class="small" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="stockFilter" style="accent-color:var(--green-700);"> In stock only</label>
      </div>
      <div class="filter-group">
        <label class="small" style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="rxFilter" style="accent-color:var(--green-700);"> Prescription Required only</label>
      </div>
      <button class="btn btn-ghost btn-block btn-sm" id="clearFilters">Clear filters</button>
    </aside>
    <div>
      <div class="med-toolbar">
        <span class="muted small" id="resultCount">Loading medicines...</span>
        <select id="sortSelect" class="field" style="margin:0;border:1px solid var(--line);border-radius:8px;padding:9px 12px;">
          <option value="top">Sort: Top Rated</option>
          <option value="low">Price: Low to High</option>
          <option value="high">Price: High to Low</option>
          <option value="name">Name A–Z</option>
        </select>
      </div>
      <div class="med-grid" id="medGrid"></div>

      <!-- Pagination Controls (Wireframe 3) -->
      <div class="pagination-bar">
        <button id="prevPageBtn" disabled>&lt; Previous</button>
        <span class="small muted" id="pageIndicator">Page 1 of 1</span>
        <button id="nextPageBtn" disabled>Next &gt;</button>
      </div>
    </div>
  </div>
</section>

<!-- ================= 3. MEDICINE DETAIL ================= -->
<section class="page" id="page-detail">
  <div class="crumb"><a data-page="home">Home</a> &gt; <a data-page="medicines">Medicines</a> &gt; <b id="crumbMedName">Medicine</b></div>
  <div class="detail-layout">
    <div class="detail-img"><svg viewBox="0 0 24 24"><path d="M10.5 20.5L3.5 13.5a5 5 0 1 1 7-7l7 7a5 5 0 1 1-7 7z"/><path d="M8.5 8.5l7 7"/></svg></div>
    <div class="detail-info">
      <span class="badge badge-green" id="detailCatBadge">Category</span>
      <h2 id="detailName" style="margin-top:10px;">Medicine Name</h2>
      <div class="mfg-line" id="detailMfg">Manufacturer: Generic</div>
      <p class="muted small" id="detailStock">In stock</p>
      <div class="rating-line">
        <span id="detailRating" style="color:var(--amber);"></span>
        <span class="muted" id="detailReviewCount"></span>
      </div>
      <div class="detail-price" id="detailPrice">₹0</div>
      <span class="badge badge-amber" id="detailRxBadge" style="display:none;">Prescription Required</span>
    </div>
    <!-- Purchase Box (Wireframe 4) -->
    <div class="card">
      <h4 style="margin-bottom:12px;font-size:14px;">Purchase Box</h4>
      <div class="qty-row">
        <button class="qty-btn" id="qtyMinus">−</button>
        <span class="qty-val" id="qtyVal">1</span>
        <button class="qty-btn" id="qtyPlus">+</button>
      </div>
      <button class="btn btn-primary btn-block" id="addToCartBtn" style="margin-bottom:10px;">Add to Cart</button>
      <button class="btn btn-outline btn-block" id="buyNowBtn">Buy Now</button>
      <div class="upload-box" style="margin-top:16px;padding:16px;" id="detailUploadPrompt">
        <p class="small">This medicine requires a prescription. <b>Upload one</b> at checkout.</p>
      </div>
    </div>
  </div>

  <!-- Description Panel (Wireframe 4: Uses / Dosage / Composition / Side Effects) -->
  <div class="tabs">
    <button class="tab-btn active" data-tab="desc">Overview</button>
    <button class="tab-btn" data-tab="uses">Uses &amp; Dosage</button>
    <button class="tab-btn" data-tab="composition">Composition &amp; Side Effects</button>
    <button class="tab-btn" data-tab="reviews">Reviews &amp; Ratings</button>
  </div>
  <div class="tab-panel active" id="tab-desc">
    <p class="muted" id="detailDesc" style="max-width:70ch;"></p>
  </div>
  <div class="tab-panel" id="tab-uses">
    <div style="max-width:70ch;" class="card">
      <h4 style="margin-bottom:8px;font-size:14.5px;">Indicated Uses</h4>
      <p class="muted small" id="detailUses" style="margin-bottom:16px;"></p>
      <h4 style="margin-bottom:8px;font-size:14.5px;">Dosage Guidelines</h4>
      <p class="muted small" id="detailDosage"></p>
    </div>
  </div>
  <div class="tab-panel" id="tab-composition">
    <div style="max-width:70ch;" class="card">
      <h4 style="margin-bottom:8px;font-size:14.5px;">Active Composition</h4>
      <p class="muted small" id="detailComposition" style="margin-bottom:16px;"></p>
      <h4 style="margin-bottom:8px;font-size:14.5px;">Possible Side Effects</h4>
      <p class="muted small" id="detailSideEffects"></p>
    </div>
  </div>
  <div class="tab-panel" id="tab-reviews">
    <div class="card" style="margin-bottom:20px;max-width:70ch;">
      <p class="small" style="font-weight:600;margin-bottom:10px;">Write a review</p>
      <div class="field" style="margin-bottom:10px;">
        <label>Your Name</label>
        <input id="revAuthor" placeholder="e.g. John D.">
      </div>
      <div class="field" style="margin-bottom:10px;">
        <label>Rating</label>
        <select id="revRating" style="border:1px solid var(--line);border-radius:8px;padding:9px;">
          <option value="5">★★★★★ 5 stars</option>
          <option value="4">★★★★☆ 4 stars</option>
          <option value="3">★★★☆☆ 3 stars</option>
        </select>
      </div>
      <textarea id="revText" class="field" rows="3" placeholder="Share your experience..." style="width:100%;border:1px solid var(--line);border-radius:8px;padding:10px;"></textarea>
      <button class="btn btn-primary btn-sm" id="submitReviewBtn">Submit Review</button>
    </div>
    <div id="reviewsList" style="max-width:70ch;"></div>
  </div>

  <h3 style="padding:0 6vw;margin-top:10px;">Related Medicines Row</h3>
  <div class="related-row" id="relatedRow"></div>
</section>

<!-- ================= 4. PROFILE ================= -->
<section class="page" id="page-profile">
  <div class="page-head">
    <h2>My Profile</h2>
    <p>Manage your details, saved addresses, order history and saved prescriptions.</p>
  </div>
  <div class="two-col">
    <div>
      <div class="card" style="margin-bottom:24px;">
        <div class="profile-head">
          <div class="avatar" id="profileAvatar">JD</div>
          <div>
            <h3 style="font-size:17px;" id="profileNameHead">John Doe</h3>
            <p class="muted small" id="profileContactHead">john@example.com &nbsp;·&nbsp; +91 98765 43210</p>
          </div>
        </div>
      </div>
      <h3 style="margin-bottom:12px;">Previous Orders</h3>
      <div class="card" style="padding:0;overflow:hidden;">
        <table>
          <thead><tr><th>Order #</th><th>Date</th><th>Items</th><th>Total</th><th></th></tr></thead>
          <tbody id="profileOrdersBody"></tbody>
        </table>
      </div>
      <h3 style="margin:26px 0 12px;">Saved Prescriptions</h3>
      <div class="rx-grid" id="profileRxGrid"></div>
    </div>
    <div class="card">
      <h4 style="margin-bottom:14px;">Default Shipping Address</h4>
      <div class="field"><label>Full Name</label><input id="profNameInput" value="John Doe"></div>
      <div class="field"><label>Email</label><input id="profEmailInput" value="john@example.com"></div>
      <div class="field"><label>Phone</label><input id="profPhoneInput" value="+91 98765 43210"></div>
      <div class="field"><label>Address</label><textarea id="profAddressInput" rows="3">44, Lotus Residency, MG Road, Kochi, Kerala 682016</textarea></div>
      <button class="btn btn-outline btn-block" id="saveProfileBtn">Save Profile &amp; Address</button>
    </div>
  </div>
</section>

<!-- ================= 5. PRESCRIPTIONS (Wireframe 5) ================= -->
<section class="page" id="page-prescriptions">
  <div class="page-head"><h2>Prescriptions Page</h2><p>Upload a prescription for verification, or track ones you've already submitted.</p></div>
  <div class="two-col">
    <div class="card">
      <h4 style="margin-bottom:16px;">Upload Section</h4>
      <div class="upload-box" id="rxUploadBox">
        <svg viewBox="0 0 24 24"><path d="M12 3v12M7 8l5-5 5 5"/><path d="M4 21h16"/></svg>
        <p><b>Click to select a file</b><br>or drag and drop (JPG, PNG, PDF)</p>
        <p id="rxFileName" class="small" style="margin-top:8px;color:var(--green-700);font-weight:600;"></p>
      </div>
      <div class="field"><label>Patient Name</label><input id="rxPatient" placeholder="Enter patient name"></div>
      <div class="field"><label>Doctor Name</label><input id="rxDoctor" placeholder="Enter prescribing doctor"></div>
      <button class="btn btn-primary btn-block" id="rxSubmitBtn">Submit for Verification</button>
    </div>
    <div class="card" style="padding:0;overflow:hidden;">
      <h4 style="padding:20px 20px 0;">My Prescriptions</h4>
      <table style="margin-top:14px;">
        <thead><tr><th>Date</th><th>Status</th><th>Linked Order</th></tr></thead>
        <tbody id="rxTableBody"></tbody>
      </table>
    </div>
  </div>
</section>

<!-- ================= 6. CART (Wireframe 6) ================= -->
<section class="page" id="page-cart">
  <div class="page-head"><h2>Cart Page</h2><p>Review your items before checking out.</p></div>
  <div class="two-col">
    <div class="card" style="padding:0;overflow:hidden;" id="cartTableWrap">
      <table>
        <thead><tr><th>Item</th><th>Price</th><th>Quantity Stepper</th><th>Subtotal</th><th></th></tr></thead>
        <tbody id="cartBody"></tbody>
      </table>
    </div>
    <div class="card">
      <h4 style="margin-bottom:10px;">Order Summary Box</h4>
      <div class="summary-line"><span>Items Total</span><span id="sumItems">₹0</span></div>
      <div class="summary-line"><span>Delivery Charge</span><span id="sumDelivery">₹40</span></div>
      <div class="summary-line"><span>Discount</span><span id="sumDiscount">−₹0</span></div>
      <div class="summary-line total"><span>Grand Total</span><span id="sumTotal">₹0</span></div>
      <button class="btn btn-primary btn-block" style="margin-top:14px;" id="checkoutBtn">Proceed to Checkout</button>
    </div>
  </div>
</section>

<!-- ================= 7. CHECKOUT (Wireframe 7) ================= -->
<section class="page" id="page-checkout">
  <div class="page-head"><h2>Checkout Page</h2><p>Confirm delivery, prescription status and payment to place your order.</p></div>
  <div class="two-col">
    <div class="card">
      <h4 style="margin-bottom:16px;">Delivery Details Form</h4>
      <div class="field"><label>Full Name</label><input id="chkName" value="John Doe"></div>
      <div class="field"><label>Address</label><textarea id="chkAddress" rows="3">44, Lotus Residency, MG Road, Kochi, Kerala 682016</textarea></div>
      <div class="field"><label>Phone Number</label><input id="chkPhone" value="+91 98765 43210"></div>
      <div class="field"><label>Delivery Time Slot</label>
        <select id="chkSlot"><option>Today, 4 PM – 7 PM</option><option>Tomorrow, 10 AM – 1 PM</option><option>Tomorrow, 2 PM – 5 PM</option></select>
      </div>

      <!-- Prescription Check (Wireframe 7) -->
      <h4 style="margin:20px 0 10px;font-size:14px;">Prescription Check</h4>
      <div class="badge badge-green" style="margin-bottom:18px;display:inline-flex;" id="chkRxStatus">Linked Prescriptions Status: Verified</div>

      <!-- Payment Section (Wireframe 7) -->
      <h4 style="margin-bottom:10px;font-size:14px;">Payment Section</h4>
      <div class="pay-options" id="payOptions">
        <button class="pay-opt selected" data-pay="card">Card</button>
        <button class="pay-opt" data-pay="upi">UPI</button>
        <button class="pay-opt" data-pay="cod">Cash on Delivery</button>
      </div>
    </div>
    <div class="card">
      <h4 style="margin-bottom:10px;">Order Summary Recap</h4>
      <div id="checkoutItems"></div>
      <div class="summary-line total"><span>Total Amount</span><span id="checkoutTotal">₹0</span></div>
      <button class="btn btn-primary btn-block" style="margin-top:14px;" id="placeOrderBtn">Place Order</button>
    </div>
  </div>
</section>

<!-- ================= 8. ORDERS (Wireframe 8) ================= -->
<section class="page" id="page-orders">
  <div class="page-head"><h2>Orders Page (Order History &amp; Tracking)</h2><p>View past orders list and track your delivery.</p></div>
  <div class="two-col">
    <div class="card" style="padding:0;overflow:hidden;">
      <h4 style="padding:16px 16px 0;font-size:14px;">Orders List</h4>
      <table style="margin-top:10px;">
        <thead><tr><th>Order ID</th><th>Date</th><th>Total</th><th>Status</th></tr></thead>
        <tbody id="ordersBody"></tbody>
      </table>
    </div>
    <div class="card" id="orderDetailCard">
      <h4 style="font-size:14.5px;">Order Detail View</h4>
      <p id="odId" class="muted small" style="margin-top:4px;">Select an order</p>
      <div class="tracker" id="odTracker"></div>
      <div id="odItems"></div>
      <button class="btn btn-outline btn-block" style="margin-top:12px;" onclick="toast('Downloading invoice PDF...')">Download Invoice</button>
    </div>
  </div>
</section>

<!-- ================= 9. ADMIN DASHBOARD ================= -->
<section class="page" id="page-admin">
  <div class="page-head" style="padding-top:32px;"><h2>Admin Dashboard</h2><p>Stock levels, expiry alerts and sales performance at a glance.</p></div>
  <div class="kpi-row">
    <div class="kpi"><span>Total Sales</span><b id="kpiSales">₹0</b></div>
    <div class="kpi"><span>Low Stock Items</span><b id="kpiLowStock">0</b></div>
    <div class="kpi"><span>Expiring Soon (30 days)</span><b id="kpiExpiring">0 batches</b></div>
    <div class="kpi"><span>Pending Rx Orders</span><b id="kpiPendingRx">0</b></div>
  </div>
  <div class="admin-section">
    <h3 style="margin-bottom:14px;">Medicine Stock &amp; Expiry Alerts</h3>
    <div class="card" style="padding:0;overflow:hidden;">
      <table>
        <thead><tr><th>Medicine Name</th><th>Batch #</th><th>Stock</th><th>Expiry Date</th><th>Alert Status</th></tr></thead>
        <tbody id="adminStockBody"></tbody>
      </table>
    </div>
  </div>
  <div class="admin-section" style="padding-top:0;">
    <h3 style="margin-bottom:14px;">Sales &amp; Revenue Analytics — Monthly Trend</h3>
    <div class="card">
      <div class="chart" id="salesChart"></div>
    </div>
  </div>
</section>

<!-- ================= 10. SUPPLIERS ================= -->
<section class="page" id="page-suppliers">
  <div class="page-head" style="padding-top:32px;"><h2>Supplier Management</h2><p>Add, edit and remove medicine suppliers.</p></div>
  <div class="two-col">
    <div class="card">
      <h4 style="margin-bottom:16px;" id="supplierFormTitle">Add Supplier</h4>
      <div class="field"><label>Supplier Name</label><input id="supName"></div>
      <div class="field"><label>Contact Person</label><input id="supContact"></div>
      <div class="field"><label>Phone Number</label><input id="supPhone"></div>
      <div class="field"><label>Email</label><input id="supEmail"></div>
      <div class="field"><label>Supplied Categories</label><input id="supCats" placeholder="e.g. Vitamins, Skin Care"></div>
      <button class="btn btn-primary btn-block" id="supSaveBtn">Save Supplier</button>
    </div>
    <div class="card" style="padding:0;overflow:hidden;">
      <h4 style="padding:20px 20px 0;">Suppliers List</h4>
      <table style="margin-top:14px;">
        <thead><tr><th>Name</th><th>Contact</th><th>Email</th><th></th></tr></thead>
        <tbody id="suppliersBody"></tbody>
      </table>
    </div>
  </div>
</section>

<!-- ================= 11. LOGIN / SIGNUP (Wireframe 8: Header minimal - Logo only) ================= -->
<section class="page" id="page-login">
  <div class="auth-wrap">
    <div class="auth-card">
      <h3 style="text-align:center;margin-bottom:16px;font-size:18px;">Login / Sign Up</h3>
      <div class="auth-tabs">
        <button class="active" data-auth="login">Login</button>
        <button data-auth="signup">Sign Up</button>
      </div>
      <div class="auth-panel active" id="auth-login">
        <div class="field"><label>Email or Phone</label><input placeholder="you@example.com"></div>
        <div class="field"><label>Password</label><input type="password" placeholder="••••••••"></div>
        <p class="small" style="text-align:right;margin-bottom:16px;"><a href="#" style="color:var(--green-700);font-weight:600;">Forgot password?</a></p>
        <button class="btn btn-primary btn-block" id="loginSubmitBtn">Login</button>
      </div>
      <div class="auth-panel" id="auth-signup">
        <div class="field"><label>Full Name</label><input placeholder="Your name"></div>
        <div class="field"><label>Email</label><input placeholder="you@example.com"></div>
        <div class="field"><label>Phone</label><input placeholder="+91"></div>
        <div class="field"><label>Password</label><input type="password"></div>
        <div class="field"><label>Confirm Password</label><input type="password"></div>
        <button class="btn btn-primary btn-block" id="signupSubmitBtn">Create Account</button>
      </div>
    </div>
  </div>
</section>

<!-- ================= 12. ABOUT (Wireframe 9) ================= -->
<section class="page" id="page-about">
  <div class="page-head"><h2>About Us Page</h2></div>
  <div class="section-pad" style="padding-top:8px;">
    <h3 style="margin-bottom:8px;font-size:18px;">Company Info Section</h3>
    <p class="muted" style="max-width:70ch;font-size:15px;">MediCart Pharmacy started with a simple goal: make it easier for people to get genuine medicines without the wait. We verify every prescription by hand, work directly with licensed suppliers, and keep our delivery network local so orders reach you quickly and safely.</p>
  </div>
  <div class="stats-row">
    <div class="stat"><b>3,500+</b><span>Medicines Available</span></div>
    <div class="stat"><b>1,200+</b><span>Prescriptions Processed</span></div>
    <div class="stat"><b>950+</b><span>Orders Delivered</span></div>
    <div class="stat"><b>2,500+</b><span>Happy Customers</span></div>
  </div>
  <div class="section-pad">
    <div class="card">
      <h4 style="margin-bottom:8px;">Team / Contact Prompt</h4>
      <p class="muted small" style="margin-bottom:14px;">Have a question for our team? Reach out any time — we typically reply within a few hours.</p>
      <button class="btn btn-outline" data-page="contact">Contact Us</button>
    </div>
  </div>
  <div class="footerContainer"></div>
</section>

<!-- ================= 13. CONTACT (Wireframe 10) ================= -->
<section class="page" id="page-contact">
  <div class="page-head"><h2>Contact Page</h2><p>Questions about an order, a medicine, or anything else — send us a message.</p></div>
  <div class="two-col">
    <div class="card">
      <h4 style="margin-bottom:16px;">Contact Form</h4>
      <div class="field"><label>Name</label><input placeholder="Your name"></div>
      <div class="field"><label>Email</label><input placeholder="you@example.com"></div>
      <div class="field"><label>Subject</label><input placeholder="How can we help?"></div>
      <div class="field"><label>Message</label><textarea rows="4" placeholder="Write your message..."></textarea></div>
      <button class="btn btn-primary" id="contactSubmitBtn">Send Message</button>
    </div>
    <div class="card">
      <h4 style="margin-bottom:14px;">Contact Details Panel</h4>
      <p class="small muted" style="margin-bottom:10px;"><b style="color:var(--ink);">Store Address</b><br>44, MG Road, Kochi, Kerala 682016</p>
      <p class="small muted" style="margin-bottom:10px;"><b style="color:var(--ink);">Phone</b><br>+91 484 234 5678</p>
      <p class="small muted" style="margin-bottom:10px;"><b style="color:var(--ink);">Email</b><br>support@medicart.example</p>
      <p class="small muted"><b style="color:var(--ink);">Working Hours</b><br>Mon – Sat, 8:00 AM – 10:00 PM</p>
    </div>
  </div>
  <div class="footerContainer"></div>
</section>

</main>

<script>
/* ================= STATE & CACHE ================= */
let categories = [];
let medicines = [];
let suppliers = [];
let orders = [];
let prescriptions = [];
let cart = [];
let currentMedicine = null;
let currentQty = 1;
let currentOrderId = null;
let selectedCategory = null;
let selectedPay = 'card';
let editingSupplierId = null;
let uploadedRxFile = 'prescription_scan.jpg';

/* ================= HELPERS ================= */
const $ = s => document.querySelector(s);
const $all = s => document.querySelectorAll(s);
const inr = n => '₹' + (n||0).toLocaleString('en-IN');
const medById = id => medicines.find(m => m.id === id);
const catName = key => (categories.find(c => c.key === key) || {}).name || key;

function toast(msg){
  const t = $('#toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => t.classList.remove('show'), 2400);
}

function stars(rating){
  const full = Math.round(rating);
  return '★'.repeat(full) + '☆'.repeat(5-full);
}

function iconSvg(path, w=26){
  return `<svg viewBox="0 0 24 24" width="${w}" height="${w}"><path d="${path}"/></svg>`;
}

/* ================= API CALLS ================= */
async function fetchAPI(endpoint, options = {}) {
  try {
    const res = await fetch('/api' + endpoint, options);
    return await res.json();
  } catch (err) {
    console.error('API Error:', err);
    return null;
  }
}

/* ================= ROUTER ================= */
async function go(page){
  $all('.page').forEach(p => p.classList.remove('active'));
  $('#page-' + page).classList.add('active');
  window.scrollTo({top:0, behavior:'instant'});

  const isAdmin = (page === 'admin' || page === 'suppliers');
  const isLogin = (page === 'login');

  $('#customerNav').style.display = isAdmin ? 'none' : 'flex';
  $('#adminNav').style.display = isAdmin ? 'flex' : 'none';

  // Wireframe 8: Header (minimal — Logo only) on Login Page
  if (isLogin) {
    $('#navLinks').style.display = 'none';
    $('#navRight').style.display = 'none';
  } else if (!isAdmin) {
    $('#navLinks').style.display = 'flex';
    $('#navRight').style.display = 'flex';
  }

  $all('#navLinks a').forEach(a => a.classList.toggle('active', a.dataset.page === page));

  if (page === 'home') loadHome();
  if (page === 'medicines') loadMedicines();
  if (page === 'orders') loadOrders();
  if (page === 'cart') renderCart();
  if (page === 'checkout') renderCheckout();
  if (page === 'admin') loadAdmin();
  if (page === 'suppliers') loadSuppliers();
  if (page === 'profile') loadProfile();
  if (page === 'prescriptions') loadPrescriptions();
}

document.body.addEventListener('click', e => {
  const el = e.target.closest('[data-page]');
  if (el){ e.preventDefault(); go(el.dataset.page); $('#navLinks').classList.remove('open'); }
});
$('#menuToggle').addEventListener('click', () => $('#navLinks').classList.toggle('open'));

/* ================= FOOTER ================= */
function renderFooters(){
  const html = `<footer class="footer">
    <div class="footer-grid">
      <div>
        <h4>MediCart Pharmacy</h4>
        <p>Genuine medicines, verified prescriptions, and fast local delivery — powered by Python & SQLite.</p>
      </div>
      <div><h4>Shop</h4><a data-page="medicines">Medicines</a><a data-page="prescriptions">Prescriptions</a><a data-page="cart">Cart</a></div>
      <div><h4>Company</h4><a data-page="about">About Us</a><a data-page="contact">Contact</a><a data-page="admin">Admin Panel</a></div>
      <div><h4>Contact</h4><p>+91 484 234 5678</p><p>support@medicart.example</p></div>
    </div>
    <div class="footer-bottom">
      <span>© 2026 MediCart Pharmacy. All rights reserved.</span>
      <span>Built strictly following Wireframe Specifications.</span>
    </div>
  </footer>`;
  $all('.footerContainer').forEach(c => c.innerHTML = html);
}

/* ================= HOME ================= */
async function loadHome(){
  categories = await fetchAPI('/categories') || [];
  $('#homeCatGrid').innerHTML = categories.map(c => {
    return `<button class="cat-chip" data-goto-cat="${c.key}">${iconSvg(c.icon)}<b>${c.name}</b><span>Explore items</span></button>`;
  }).join('');

  const stats = await fetchAPI('/stats');
  if(stats){
    $('#statMedCount').textContent = stats.medicines + '+';
    $('#statRxCount').textContent = stats.prescriptions + '+';
    $('#statOrderCount').textContent = stats.orders + '+';
  }
}

document.body.addEventListener('click', e => {
  const el = e.target.closest('[data-goto-cat]');
  if (el){ selectedCategory = el.dataset.gotoCat; go('medicines'); }
});

/* ================= MEDICINES PAGE (Wireframe 3) ================= */
async function loadMedicines(){
  categories = await fetchAPI('/categories') || [];
  $('#filterCategories').innerHTML = categories.map(c =>
    `<label><input type="checkbox" class="catCheck" value="${c.key}" ${selectedCategory===c.key?'checked':''}> ${c.name}</label>`
  ).join('');
  fetchFilteredMedicines();
}

async function fetchFilteredMedicines(){
  const q = ($('#searchInput').value || $('#catSearchInput').value || '').toLowerCase().trim();
  const checked = [...$all('.catCheck:checked')].map(c => c.value);
  const maxPrice = Number($('#priceRange').value);
  const ratingOnly = $('#ratingFilter').checked ? '1' : '0';
  const stockOnly = $('#stockFilter').checked ? '1' : '0';
  const rxOnly = $('#rxFilter').checked ? '1' : '0';
  const sort = $('#sortSelect').value;

  const params = new URLSearchParams({
    q, cat: checked.join(','), max_price: maxPrice, rating_only: ratingOnly, stock_only: stockOnly, rx_only: rxOnly, sort
  });

  medicines = await fetchAPI('/medicines?' + params.toString()) || [];
  renderMedicinesGrid();
}

function renderMedicinesGrid(){
  $('#medGrid').innerHTML = medicines.map(m => {
    const stockLabel = m.stock === 0 ? '<span class="badge badge-red">Out of stock</span>' : (m.stock < 20 ? '<span class="badge badge-amber">Low stock</span>' : '');
    const rxTag = m.rx ? '<span class="badge badge-amber" style="font-size:10.5px;">Rx</span>' : '';
    return `<div class="med-card" data-open-med="${m.id}">
      <div class="med-thumb">${iconSvg('M10.5 20.5L3.5 13.5a5 5 0 1 1 7-7l7 7a5 5 0 1 1-7 7z M8.5 8.5l7 7', 34)}</div>
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:4px;">
        <h4>${m.name}</h4>
        ${rxTag}
      </div>
      <div class="med-mfg">by ${m.manufacturer || 'Generic'}</div>
      <div class="med-rating">${stars(m.rating)} <span>${m.rating} (${m.reviews})</span></div>
      ${stockLabel}
      <div class="med-price-row">
        <span class="med-price">${inr(m.price)}</span>
        <button class="btn btn-primary btn-sm" data-quick-add="${m.id}" ${m.stock===0?'disabled style="opacity:.5;cursor:not-allowed;"':''}>Add to Cart</button>
      </div>
    </div>`;
  }).join('') || '<p class="muted">No medicines match these filters.</p>';

  $('#resultCount').textContent = `${medicines.length} medicine${medicines.length===1?'':'s'}`;
  $('#pageIndicator').textContent = `Page 1 of ${Math.ceil(medicines.length/12) || 1}`;
}

['input','change'].forEach(evt => {
  $('#searchInput').addEventListener(evt, () => { if($('#page-medicines').classList.contains('active')) fetchFilteredMedicines(); });
  $('#catSearchInput').addEventListener(evt, () => {
    $('#searchInput').value = $('#catSearchInput').value;
    if($('#page-medicines').classList.contains('active')) fetchFilteredMedicines();
  });
});
$('#priceRange').addEventListener('input', () => { $('#priceVal').textContent = $('#priceRange').value; fetchFilteredMedicines(); });
$('#ratingFilter').addEventListener('change', fetchFilteredMedicines);
$('#stockFilter').addEventListener('change', fetchFilteredMedicines);
$('#rxFilter').addEventListener('change', fetchFilteredMedicines);
$('#sortSelect').addEventListener('change', fetchFilteredMedicines);

$('#clearFilters').addEventListener('click', () => {
  selectedCategory = null;
  $('#priceRange').value = 300; $('#priceVal').textContent = 300;
  $('#ratingFilter').checked = false; $('#stockFilter').checked = false; $('#rxFilter').checked = false;
  $('#searchInput').value = ''; $('#catSearchInput').value = '';
  fetchFilteredMedicines();
});

document.body.addEventListener('change', e => {
  if (e.target.classList.contains('catCheck')) fetchFilteredMedicines();
});
document.body.addEventListener('click', e => {
  const openEl = e.target.closest('[data-open-med]');
  if (openEl){ openDetail(Number(openEl.dataset.openMed)); return; }
  const quickAdd = e.target.closest('[data-quick-add]');
  if (quickAdd){ e.stopPropagation(); addToCart(Number(quickAdd.dataset.quickAdd), 1); }
});

/* ================= DETAIL PAGE (Wireframe 4) ================= */
async function openDetail(id){
  const data = await fetchAPI('/medicines/' + id);
  if (!data) return;
  currentMedicine = data.medicine;
  currentQty = 1;

  $('#crumbMedName').textContent = currentMedicine.name;
  $('#detailCatBadge').textContent = catName(currentMedicine.cat);
  $('#detailName').textContent = currentMedicine.name;
  $('#detailMfg').textContent = 'Manufacturer: ' + (currentMedicine.manufacturer || 'Generic Pharma');
  $('#detailStock').textContent = currentMedicine.stock === 0 ? 'Out of stock' : (currentMedicine.stock < 20 ? `Only ${currentMedicine.stock} left in stock` : 'In stock');
  $('#detailRating').textContent = stars(currentMedicine.rating) + ' ' + currentMedicine.rating;
  $('#detailReviewCount').textContent = `(${currentMedicine.reviews} reviews)`;
  $('#detailPrice').textContent = inr(currentMedicine.price);
  $('#detailRxBadge').style.display = currentMedicine.rx ? 'inline-flex' : 'none';
  $('#detailUploadPrompt').style.display = currentMedicine.rx ? 'block' : 'none';
  $('#detailDesc').textContent = currentMedicine.desc;
  $('#detailUses').textContent = currentMedicine.uses || 'Used for pain relief and symptomatic reduction under doctor supervision.';
  $('#detailDosage').textContent = currentMedicine.dosage || 'As directed by physician.';
  $('#detailComposition').textContent = currentMedicine.composition || 'Active pharmacopoeial grade ingredients.';
  $('#detailSideEffects').textContent = currentMedicine.side_effects || 'Mild gastrointestinal discomfort in rare cases.';
  $('#qtyVal').textContent = currentQty;

  $('#reviewsList').innerHTML = data.reviews.map(r =>
    `<div class="review"><div class="review-head"><span>${r.name}</span><span style="color:var(--amber);">${stars(r.rating)}</span></div><p class="small muted">${r.text}</p></div>`
  ).join('') || '<p class="muted small">No reviews yet. Be the first to leave one!</p>';

  $('#relatedRow').innerHTML = data.related.map(r =>
    `<button class="med-card" data-open-med="${r.id}"><div class="med-thumb">${iconSvg('M10.5 20.5L3.5 13.5a5 5 0 1 1 7-7l7 7a5 5 0 1 1-7 7z',26)}</div><h4 class="small">${r.name}</h4><span class="med-price">${inr(r.price)}</span></button>`
  ).join('');

  $all('.tab-btn').forEach(b => b.classList.remove('active'));
  $('.tab-btn[data-tab="desc"]').classList.add('active');
  $all('.tab-panel').forEach(p => p.classList.remove('active'));
  $('#tab-desc').classList.add('active');

  go('detail');
}

$('#qtyMinus').addEventListener('click', () => { currentQty = Math.max(1, currentQty-1); $('#qtyVal').textContent = currentQty; });
$('#qtyPlus').addEventListener('click', () => { currentQty += 1; $('#qtyVal').textContent = currentQty; });
$('#addToCartBtn').addEventListener('click', () => { addToCart(currentMedicine.id, currentQty); });
$('#buyNowBtn').addEventListener('click', () => { addToCart(currentMedicine.id, currentQty); go('cart'); });

$('#submitReviewBtn').addEventListener('click', async () => {
  const name = $('#revAuthor').value.trim() || 'Anonymous';
  const rating = Number($('#revRating').value);
  const text = $('#revText').value.trim();
  if(!text){ toast('Please write a review text'); return; }

  const res = await fetchAPI('/medicines/' + currentMedicine.id + '/reviews', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({name, rating, text})
  });
  if(res && res.success){
    toast('Review submitted successfully');
    $('#revText').value = '';
    openDetail(currentMedicine.id);
  }
});

$all('.tab-btn').forEach(btn => btn.addEventListener('click', () => {
  $all('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  $all('.tab-panel').forEach(p => p.classList.remove('active'));
  $('#tab-' + btn.dataset.tab).classList.add('active');
}));

/* ================= CART (Wireframe 6) ================= */
function addToCart(id, qty){
  const existing = cart.find(c => c.id === id);
  if (existing) existing.qty += qty; else cart.push({id, qty});
  updateCartCount();
  toast('Added to cart');
}

function updateCartCount(){
  $('#cartCount').textContent = cart.reduce((s,c) => s + c.qty, 0);
}

function cartTotal(){
  return cart.reduce((s,c) => {
    const m = medById(c.id);
    return s + (m ? m.price * c.qty : 0);
  }, 0);
}

function renderCart(){
  if (!cart.length){
    $('#cartBody').innerHTML = `<tr><td colspan="5" class="muted" style="text-align:center;padding:36px;">Your cart is empty. <a data-page="medicines" style="color:var(--green-700);font-weight:600;">Browse medicines →</a></td></tr>`;
  } else {
    $('#cartBody').innerHTML = cart.map(c => {
      const m = medById(c.id) || {name:'Item', price:0};
      return `<tr>
        <td>${m.name}</td>
        <td>${inr(m.price)}</td>
        <td>
          <div style="display:flex;align-items:center;gap:8px;">
            <button class="qty-btn" data-cart-dec="${c.id}">−</button>
            <span class="qty-val">${c.qty}</span>
            <button class="qty-btn" data-cart-inc="${c.id}">+</button>
          </div>
        </td>
        <td>${inr(m.price * c.qty)}</td>
        <td><button class="btn btn-danger btn-sm" data-cart-remove="${c.id}">Remove</button></td>
      </tr>`;
    }).join('');
  }
  const items = cartTotal();
  const delivery = items > 0 ? 40 : 0;
  $('#sumItems').textContent = inr(items);
  $('#sumDelivery').textContent = inr(delivery);
  $('#sumTotal').textContent = inr(items + delivery);
}

document.body.addEventListener('click', e => {
  const inc = e.target.closest('[data-cart-inc]');
  const dec = e.target.closest('[data-cart-dec]');
  const rem = e.target.closest('[data-cart-remove]');
  if (inc){ cart.find(c=>c.id===Number(inc.dataset.cartInc)).qty++; updateCartCount(); renderCart(); }
  if (dec){
    const item = cart.find(c=>c.id===Number(dec.dataset.cartDec));
    item.qty = Math.max(1, item.qty-1);
    updateCartCount(); renderCart();
  }
  if (rem){
    cart = cart.filter(c => c.id !== Number(rem.dataset.cartRemove));
    updateCartCount(); renderCart();
  }
});

$('#checkoutBtn').addEventListener('click', () => {
  if (!cart.length){ toast('Your cart is empty'); return; }
  go('checkout');
});

/* ================= CHECKOUT (Wireframe 7) ================= */
function renderCheckout(){
  $('#checkoutItems').innerHTML = cart.map(c => {
    const m = medById(c.id) || {name:'Item', price:0};
    return `<div class="summary-line"><span>${m.name} × ${c.qty}</span><span>${inr(m.price*c.qty)}</span></div>`;
  }).join('') || '<p class="muted small">No items in cart.</p>';
  const total = cartTotal() + (cart.length ? 40 : 0);
  $('#checkoutTotal').textContent = inr(total);

  const hasRx = cart.some(c => {
    const m = medById(c.id);
    return m && m.rx;
  });
  $('#chkRxStatus').textContent = hasRx ? 'Prescription Check: Linked & Verified for Order' : 'Prescription Check: Not Required for Selected Items';
}

$all('.pay-opt').forEach(btn => btn.addEventListener('click', () => {
  $all('.pay-opt').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedPay = btn.dataset.pay;
}));

$('#placeOrderBtn').addEventListener('click', async () => {
  if (!cart.length){ toast('Your cart is empty'); return; }
  const address = $('#chkAddress').value.trim();
  const res = await fetchAPI('/orders', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({
      items: cart,
      address,
      payment_method: selectedPay
    })
  });
  if (res && res.order_id){
    cart = [];
    updateCartCount();
    currentOrderId = res.order_id;
    toast('Order placed successfully! ID: ' + res.order_id);
    go('orders');
  }
});

/* ================= ORDERS (Wireframe 8) ================= */
const STATUS_STEPS = ['Placed','Packed','Shipped','Delivered'];
async function loadOrders(){
  orders = await fetchAPI('/orders') || [];
  $('#ordersBody').innerHTML = orders.map(o =>
    `<tr data-select-order="${o.id}" style="cursor:pointer;"><td>${o.id}</td><td>${o.date}</td><td>${inr(o.total)}</td><td><span class="badge badge-green">${o.status}</span></td></tr>`
  ).join('');
  if (!currentOrderId && orders.length) currentOrderId = orders[0].id;
  renderOrderDetail();
}

function renderOrderDetail(){
  const o = orders.find(x => x.id === currentOrderId);
  if (!o){ $('#odId').textContent = 'No orders yet'; $('#odTracker').innerHTML=''; $('#odItems').innerHTML=''; return; }
  $('#odId').textContent = `${o.id} — ${o.date}`;
  const currentIdx = STATUS_STEPS.indexOf(o.status);
  $('#odTracker').innerHTML = STATUS_STEPS.map((s,i) =>
    `<div class="step ${i<=currentIdx?'done':''}"><div class="line"></div><div class="dot"></div><span>${s}</span></div>`
  ).join('');
  $('#odItems').innerHTML = '<div class="divider"></div>' + o.items.map(it => {
    return `<div class="summary-line"><span>${it.name} × ${it.qty}</span><span>${inr(it.price*it.qty)}</span></div>`;
  }).join('') + `<div class="summary-line total"><span>Total</span><span>${inr(o.total)}</span></div>`;
}

document.body.addEventListener('click', e => {
  const row = e.target.closest('[data-select-order]');
  if (row){ currentOrderId = row.dataset.selectOrder; renderOrderDetail(); }
});

/* ================= PROFILE ================= */
async function loadProfile(){
  const user = await fetchAPI('/user/profile');
  if(user){
    $('#profileNameHead').textContent = user.name;
    $('#profileContactHead').textContent = `${user.email} · ${user.phone}`;
    $('#profNameInput').value = user.name;
    $('#profEmailInput').value = user.email;
    $('#profPhoneInput').value = user.phone;
    $('#profAddressInput').value = user.address;
    $('#profileAvatar').textContent = user.name.split(' ').map(n=>n[0]).join('').toUpperCase();
  }

  orders = await fetchAPI('/orders') || [];
  $('#profileOrdersBody').innerHTML = orders.map(o =>
    `<tr><td>${o.id}</td><td>${o.date}</td><td>${o.items.length} item${o.items.length===1?'':'s'}</td><td>${inr(o.total)}</td><td><button class="btn btn-ghost btn-sm" data-view-order="${o.id}">View</button></td></tr>`
  ).join('');

  prescriptions = await fetchAPI('/prescriptions') || [];
  $('#profileRxGrid').innerHTML = prescriptions.map(p =>
    `<div class="rx-doc">${iconSvg('M4 21h16M6 21V7l6-4 6 4v14', 20)}<span>${p.file}</span></div>`
  ).join('');
}

$('#saveProfileBtn').addEventListener('click', async () => {
  const name = $('#profNameInput').value;
  const email = $('#profEmailInput').value;
  const phone = $('#profPhoneInput').value;
  const address = $('#profAddressInput').value;
  const res = await fetchAPI('/user/profile', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({name, email, phone, address})
  });
  if(res && res.success){
    toast('Profile updated successfully');
    loadProfile();
  }
});

document.body.addEventListener('click', e => {
  const v = e.target.closest('[data-view-order]');
  if (v){ currentOrderId = v.dataset.viewOrder; go('orders'); }
});

/* ================= PRESCRIPTIONS (Wireframe 5) ================= */
$('#rxUploadBox').addEventListener('click', () => {
  uploadedRxFile = 'prescription_' + Math.floor(Math.random()*1000) + '.jpg';
  $('#rxFileName').textContent = 'Selected: ' + uploadedRxFile;
});

$('#rxSubmitBtn').addEventListener('click', async () => {
  const patient = $('#rxPatient').value.trim();
  const doctor = $('#rxDoctor').value.trim();
  if (!patient || !doctor){ toast('Please fill in patient and doctor name'); return; }

  const res = await fetchAPI('/prescriptions', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({file: uploadedRxFile, patient, doctor})
  });
  if(res && res.success){
    $('#rxPatient').value=''; $('#rxDoctor').value=''; $('#rxFileName').textContent='';
    toast('Prescription submitted for verification');
    loadPrescriptions();
  }
});

async function loadPrescriptions(){
  prescriptions = await fetchAPI('/prescriptions') || [];
  $('#rxTableBody').innerHTML = prescriptions.map(p => {
    const badge = p.status === 'Verified' ? 'badge-green' : (p.status === 'Rejected' ? 'badge-red' : 'badge-amber');
    return `<tr><td>${p.date}</td><td><span class="badge ${badge}">${p.status}</span></td><td>${p.order_id || '—'}</td></tr>`;
  }).join('');
}

/* ================= ADMIN ================= */
async function loadAdmin(){
  const dash = await fetchAPI('/admin/dashboard');
  if(!dash) return;

  $('#kpiSales').textContent = inr(dash.kpis.total_sales);
  $('#kpiLowStock').textContent = dash.kpis.low_stock;
  $('#kpiExpiring').textContent = dash.kpis.expiring + ' batches';
  $('#kpiPendingRx').textContent = dash.kpis.pending_rx;

  $('#adminStockBody').innerHTML = dash.stock.map(s => {
    let badge = '<span class="badge badge-green">OK</span>';
    if (s.status === 'low') badge = '<span class="badge badge-amber">Low Stock</span>';
    if (s.status === 'expiring') badge = '<span class="badge badge-amber">Expiring Soon</span>';
    if (s.status === 'out') badge = '<span class="badge badge-red">Out of Stock</span>';
    return `<tr><td>${s.name}</td><td>${s.batch}</td><td>${s.stock}</td><td>${s.expiry}</td><td>${badge}</td></tr>`;
  }).join('');

  const months = dash.monthly;
  const max = Math.max(...months.map(m=>m[1]), 1);
  $('#salesChart').innerHTML = months.map(([label,val]) =>
    `<div class="bar-wrap"><div class="bar" style="height:${(val/max*100)}%;"></div><span>${label}</span></div>`
  ).join('');
}

/* ================= SUPPLIERS ================= */
async function loadSuppliers(){
  suppliers = await fetchAPI('/suppliers') || [];
  $('#suppliersBody').innerHTML = suppliers.map(s =>
    `<tr><td>${s.name}</td><td>${s.contact}</td><td>${s.email}</td>
     <td style="white-space:nowrap;">
       <button class="btn btn-ghost btn-sm" data-edit-sup="${s.id}">Edit</button>
       <button class="btn btn-danger btn-sm" data-del-sup="${s.id}">Delete</button>
     </td></tr>`
  ).join('');
}

$('#supSaveBtn').addEventListener('click', async () => {
  const name = $('#supName').value.trim();
  if (!name){ toast('Supplier name is required'); return; }
  const payload = {
    name,
    contact: $('#supContact').value.trim(),
    phone: $('#supPhone').value.trim(),
    email: $('#supEmail').value.trim(),
    cats: $('#supCats').value.trim(),
  };

  if (editingSupplierId){
    await fetchAPI('/suppliers/' + editingSupplierId, {
      method: 'PUT',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    toast('Supplier updated');
    editingSupplierId = null;
    $('#supplierFormTitle').textContent = 'Add Supplier';
  } else {
    await fetchAPI('/suppliers', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    toast('Supplier added');
  }
  ['supName','supContact','supPhone','supEmail','supCats'].forEach(id => $('#'+id).value = '');
  loadSuppliers();
});

document.body.addEventListener('click', async e => {
  const edit = e.target.closest('[data-edit-sup]');
  const del = e.target.closest('[data-del-sup]');
  if (edit){
    const s = suppliers.find(x => x.id === Number(edit.dataset.editSup));
    if (s){
      editingSupplierId = s.id;
      $('#supName').value = s.name; $('#supContact').value = s.contact;
      $('#supPhone').value = s.phone; $('#supEmail').value = s.email; $('#supCats').value = s.cats;
      $('#supplierFormTitle').textContent = 'Edit Supplier';
    }
  }
  if (del){
    await fetchAPI('/suppliers/' + Number(del.dataset.delSup), { method:'DELETE' });
    toast('Supplier removed');
    loadSuppliers();
  }
});

/* ================= LOGIN / SIGNUP ================= */
$all('.auth-tabs button').forEach(btn => btn.addEventListener('click', () => {
  $all('.auth-tabs button').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  $all('.auth-panel').forEach(p => p.classList.remove('active'));
  $('#auth-' + btn.dataset.auth).classList.add('active');
}));

$('#loginSubmitBtn').addEventListener('click', () => {
  toast('Logged in successfully');
  $('#accountBtn').textContent = 'John Doe';
  $('#accountBtn').dataset.page = 'profile';
  go('profile');
});

$('#signupSubmitBtn').addEventListener('click', () => {
  toast('Account created — please log in');
  $all('.auth-tabs button').forEach(b => b.classList.remove('active'));
  $('.auth-tabs button[data-auth="login"]').classList.add('active');
  $all('.auth-panel').forEach(p => p.classList.remove('active'));
  $('#auth-login').classList.add('active');
});

/* ================= CONTACT ================= */
$('#contactSubmitBtn').addEventListener('click', () => toast('Message sent — we\'ll get back to you soon.'));

/* ================= INIT ================= */
renderFooters();
go('home');
</script>
</body>
</html>
"""

class PharmacyAPIHandler(http.server.BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def parse_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode('utf-8')
        return json.loads(raw) if raw else {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not path.startswith('/api'):
            self.send_html(HTML_PAGE)
            return

        conn = get_db()
        cursor = conn.cursor()

        if path == '/api/categories':
            cursor.execute("SELECT * FROM categories")
            rows = [dict(r) for r in cursor.fetchall()]
            self.send_json(rows)
            conn.close()
            return

        if path == '/api/stats':
            cursor.execute("SELECT COUNT(*) FROM medicines")
            meds = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM prescriptions")
            rxs = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM orders")
            ords = cursor.fetchone()[0]
            self.send_json({'medicines': meds, 'prescriptions': rxs, 'orders': ords})
            conn.close()
            return

        if path == '/api/medicines':
            q = query.get('q', [''])[0].strip().lower()
            cats = query.get('cat', [''])[0].split(',') if query.get('cat', [''])[0] else []
            max_price = float(query.get('max_price', [9999])[0])
            rating_only = query.get('rating_only', ['0'])[0] == '1'
            stock_only = query.get('stock_only', ['0'])[0] == '1'
            rx_only = query.get('rx_only', ['0'])[0] == '1'
            sort = query.get('sort', ['top'])[0]

            sql = "SELECT * FROM medicines WHERE price <= ?"
            params = [max_price]

            if cats:
                sql += f" AND cat IN ({','.join(['?']*len(cats))})"
                params.extend(cats)
            if rating_only:
                sql += " AND rating >= 4.0"
            if stock_only:
                sql += " AND stock > 0"
            if rx_only:
                sql += " AND rx = 1"

            cursor.execute(sql, params)
            rows = [dict(r) for r in cursor.fetchall()]

            if q:
                rows = [r for r in rows if q in r['name'].lower() or q in r['desc'].lower() or q in (r.get('manufacturer') or '').lower()]

            if sort == 'low':
                rows.sort(key=lambda x: x['price'])
            elif sort == 'high':
                rows.sort(key=lambda x: x['price'], reverse=True)
            elif sort == 'name':
                rows.sort(key=lambda x: x['name'])
            else:
                rows.sort(key=lambda x: x['rating'], reverse=True)

            self.send_json(rows)
            conn.close()
            return

        if path.startswith('/api/medicines/'):
            parts = path.split('/')
            med_id = int(parts[3])
            cursor.execute("SELECT * FROM medicines WHERE id = ?", (med_id,))
            med = cursor.fetchone()
            if not med:
                self.send_json({'error': 'Not found'}, status=404)
                conn.close()
                return

            med_dict = dict(med)
            cursor.execute("SELECT * FROM reviews WHERE medicine_id = ? ORDER BY id DESC", (med_id,))
            reviews = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM medicines WHERE cat = ? AND id != ? LIMIT 4", (med_dict['cat'], med_id))
            related = [dict(r) for r in cursor.fetchall()]

            self.send_json({'medicine': med_dict, 'reviews': reviews, 'related': related})
            conn.close()
            return

        if path == '/api/suppliers':
            cursor.execute("SELECT * FROM suppliers ORDER BY id DESC")
            rows = [dict(r) for r in cursor.fetchall()]
            self.send_json(rows)
            conn.close()
            return

        if path == '/api/orders':
            cursor.execute("SELECT * FROM orders ORDER BY date DESC, id DESC")
            orders_list = []
            for row in cursor.fetchall():
                od = dict(row)
                cursor.execute("""
                    SELECT oi.*, m.name FROM order_items oi
                    JOIN medicines m ON oi.medicine_id = m.id
                    WHERE oi.order_id = ?
                """, (od['id'],))
                od['items'] = [dict(item) for item in cursor.fetchall()]
                orders_list.append(od)
            self.send_json(orders_list)
            conn.close()
            return

        if path == '/api/prescriptions':
            cursor.execute("SELECT * FROM prescriptions ORDER BY id DESC")
            rows = [dict(r) for r in cursor.fetchall()]
            self.send_json(rows)
            conn.close()
            return

        if path == '/api/user/profile':
            cursor.execute("SELECT * FROM user_profile WHERE id = 1")
            user = dict(cursor.fetchone())
            self.send_json(user)
            conn.close()
            return

        if path == '/api/admin/dashboard':
            cursor.execute("SELECT SUM(total) FROM orders")
            total_sales = cursor.fetchone()[0] or 0.0
            cursor.execute("SELECT COUNT(*) FROM medicines WHERE stock < 20")
            low_stock = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM admin_stock WHERE status = 'expiring'")
            expiring = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM prescriptions WHERE status = 'Pending'")
            pending_rx = cursor.fetchone()[0]

            cursor.execute("SELECT * FROM admin_stock")
            stock_items = [dict(r) for r in cursor.fetchall()]

            monthly = [('Mar', 28000), ('Apr', 34000), ('May', 31000), ('Jun', 42000), ('Jul', 38000), ('Aug', 45200)]

            self.send_json({
                'kpis': {
                    'total_sales': total_sales,
                    'low_stock': low_stock,
                    'expiring': expiring,
                    'pending_rx': pending_rx
                },
                'stock': stock_items,
                'monthly': monthly
            })
            conn.close()
            return

        self.send_json({'error': 'Endpoint not found'}, status=404)
        conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        data = self.parse_body()

        conn = get_db()
        cursor = conn.cursor()

        if path == '/api/orders':
            items = data.get('items', [])
            address = data.get('address', '')
            pay_method = data.get('payment_method', 'card')

            cursor.execute("SELECT COUNT(*) FROM orders")
            count = cursor.fetchone()[0] + 1089
            order_id = f"ORD-{count}"

            items_total = 0.0
            for item in items:
                cursor.execute("SELECT price, stock FROM medicines WHERE id = ?", (item['id'],))
                row = cursor.fetchone()
                if row:
                    price, stock = row[0], row[1]
                    items_total += price * item['qty']
                    new_stock = max(0, stock - item['qty'])
                    cursor.execute("UPDATE medicines SET stock = ? WHERE id = ?", (new_stock, item['id']))
                    cursor.execute("INSERT INTO order_items (order_id, medicine_id, qty, price) VALUES (?,?,?,?)",
                                   (order_id, item['id'], item['qty'], price))

            total = items_total + (40.0 if items else 0.0)
            cursor.execute("INSERT INTO orders VALUES (?, date('now'), ?, 'Placed', ?, ?)",
                           (order_id, total, address, pay_method))

            conn.commit()
            self.send_json({'success': True, 'order_id': order_id, 'total': total})
            conn.close()
            return

        if path.startswith('/api/medicines/') and path.endswith('/reviews'):
            med_id = int(path.split('/')[3])
            name = data.get('name', 'Anonymous')
            rating = int(data.get('rating', 5))
            text = data.get('text', '')

            cursor.execute("INSERT INTO reviews (medicine_id, name, rating, text, date) VALUES (?,?,?,?, date('now'))",
                           (med_id, name, rating, text))
            cursor.execute("UPDATE medicines SET reviews = reviews + 1 WHERE id = ?", (med_id,))
            conn.commit()
            self.send_json({'success': True})
            conn.close()
            return

        if path == '/api/suppliers':
            name = data.get('name', '')
            contact = data.get('contact', '')
            phone = data.get('phone', '')
            email = data.get('email', '')
            cats = data.get('cats', '')

            cursor.execute("INSERT INTO suppliers (name, contact, phone, email, cats) VALUES (?,?,?,?,?)",
                           (name, contact, phone, email, cats))
            conn.commit()
            self.send_json({'success': True, 'id': cursor.lastrowid})
            conn.close()
            return

        if path == '/api/prescriptions':
            filename = data.get('file', 'prescription.jpg')
            patient = data.get('patient', '')
            doctor = data.get('doctor', '')

            cursor.execute("INSERT INTO prescriptions (file, patient, doctor, date, status, order_id) VALUES (?,?,?, date('now'), 'Pending', '—')",
                           (filename, patient, doctor))
            conn.commit()
            self.send_json({'success': True})
            conn.close()
            return

        if path == '/api/user/profile':
            name = data.get('name', '')
            email = data.get('email', '')
            phone = data.get('phone', '')
            address = data.get('address', '')

            cursor.execute("UPDATE user_profile SET name=?, email=?, phone=?, address=? WHERE id=1",
                           (name, email, phone, address))
            conn.commit()
            self.send_json({'success': True})
            conn.close()
            return

        self.send_json({'error': 'Endpoint not found'}, status=404)
        conn.close()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        data = self.parse_body()

        conn = get_db()
        cursor = conn.cursor()

        if path.startswith('/api/suppliers/'):
            sup_id = int(path.split('/')[3])
            name = data.get('name', '')
            contact = data.get('contact', '')
            phone = data.get('phone', '')
            email = data.get('email', '')
            cats = data.get('cats', '')

            cursor.execute("UPDATE suppliers SET name=?, contact=?, phone=?, email=?, cats=? WHERE id=?",
                           (name, contact, phone, email, cats, sup_id))
            conn.commit()
            self.send_json({'success': True})
            conn.close()
            return

        self.send_json({'error': 'Endpoint not found'}, status=404)
        conn.close()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        conn = get_db()
        cursor = conn.cursor()

        if path.startswith('/api/suppliers/'):
            sup_id = int(path.split('/')[3])
            cursor.execute("DELETE FROM suppliers WHERE id = ?", (sup_id,))
            conn.commit()
            self.send_json({'success': True})
            conn.close()
            return

        self.send_json({'error': 'Endpoint not found'}, status=404)
        conn.close()

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

def run_server():
    init_db()
    httpd = None
    port = PORT
    for try_port in range(PORT, PORT + 10):
        try:
            httpd = ReusableTCPServer(("", try_port), PharmacyAPIHandler)
            port = try_port
            break
        except OSError:
            continue

    if not httpd:
        print(f"Error: Could not bind to any port in range {PORT}-{PORT+9}.")
        return

    url = f"http://127.0.0.1:{port}"
    print(f"==================================================")
    print(f" MediCart Pharmacy Server active at: {url}")
    print(f" SQLite Database: {DB_FILE}")
    print(f"==================================================")
    webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")

if __name__ == "__main__":
    run_server()
