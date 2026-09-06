
"""
MediCart Pharmacy — DBMS Project
==================================
10-table normalized SQLite schema (3NF), SHA-256 hashing, audit log,
role-based access, sales/stock reports. Zero external dependencies.

Run:   python index.py
URL:   http://localhost:8000/

Credentials:
  Master Admin  master@medicart.com  / master123
  Pharmacist    admin@medicart.com   / admin123
  Customer      john@example.com     / password123
"""
import os, json, sqlite3, hashlib, webbrowser, threading, re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pharmacy_dbms.db')
PORT = 8000
PW_SALT = 'MediCart_DBMS_2026'

def hash_pw(pw):
    return hashlib.sha256((PW_SALT + pw).encode()).hexdigest()

def check_pw(plain, stored):
    return stored == hash_pw(plain) or stored == plain

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def audit(conn, action, entity, entity_id, user_email='system', user_type='system', details=''):
    try:
        conn.execute(
            'INSERT INTO audit_log (action,entity,entity_id,user_email,user_type,timestamp,details) VALUES (?,?,?,?,?,?,?)',
            (action, entity, str(entity_id), user_email, user_type, datetime.now().isoformat(), details)
        )
        conn.commit()
    except Exception:
        pass

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript(
        "CREATE TABLE IF NOT EXISTS categories ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT UNIQUE NOT NULL, name TEXT NOT NULL,"
        "icon TEXT NOT NULL DEFAULT '💊', description TEXT NOT NULL DEFAULT '');"

        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,"
        "phone TEXT NOT NULL DEFAULT '', password_hash TEXT NOT NULL,"
        "address TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);"

        "CREATE TABLE IF NOT EXISTS admins ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,"
        "phone TEXT NOT NULL DEFAULT '', password_hash TEXT NOT NULL,"
        "role TEXT NOT NULL DEFAULT 'Pharmacist', is_master INTEGER NOT NULL DEFAULT 0,"
        "created_at TEXT NOT NULL);"

        "CREATE TABLE IF NOT EXISTS medicines ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, category_id INTEGER NOT NULL,"
        "price REAL NOT NULL, rating REAL NOT NULL DEFAULT 4.5, reviews INTEGER NOT NULL DEFAULT 0,"
        "stock INTEGER NOT NULL DEFAULT 0, rx_required INTEGER NOT NULL DEFAULT 0,"
        "manufacturer TEXT NOT NULL, description TEXT NOT NULL,"
        "FOREIGN KEY (category_id) REFERENCES categories(id));"

        "CREATE TABLE IF NOT EXISTS orders ("
        "id TEXT PRIMARY KEY, user_email TEXT NOT NULL, date TEXT NOT NULL,"
        "total REAL NOT NULL, status TEXT NOT NULL DEFAULT 'Placed',"
        "delivery_name TEXT NOT NULL DEFAULT '', delivery_address TEXT NOT NULL DEFAULT '',"
        "delivery_phone TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);"

        "CREATE TABLE IF NOT EXISTS order_items ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT NOT NULL,"
        "medicine_id INTEGER NOT NULL, quantity INTEGER NOT NULL, unit_price REAL NOT NULL,"
        "FOREIGN KEY (order_id) REFERENCES orders(id),"
        "FOREIGN KEY (medicine_id) REFERENCES medicines(id));"

        "CREATE TABLE IF NOT EXISTS prescriptions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT NOT NULL,"
        "patient_name TEXT NOT NULL, doctor_name TEXT NOT NULL, date TEXT NOT NULL,"
        "status TEXT NOT NULL DEFAULT 'Pending', order_id TEXT NOT NULL DEFAULT '',"
        "user_email TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '');"

        "CREATE TABLE IF NOT EXISTS suppliers ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,"
        "contact_person TEXT NOT NULL, phone TEXT NOT NULL, email TEXT NOT NULL,"
        "categories TEXT NOT NULL, address TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL);"

        "CREATE TABLE IF NOT EXISTS stock_batches ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, medicine_id INTEGER NOT NULL,"
        "batch_no TEXT NOT NULL, quantity INTEGER NOT NULL, expiry_date TEXT NOT NULL,"
        "status TEXT NOT NULL DEFAULT 'ok', received_date TEXT NOT NULL, supplier_id INTEGER,"
        "FOREIGN KEY (medicine_id) REFERENCES medicines(id));"

        "CREATE TABLE IF NOT EXISTS audit_log ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, entity TEXT NOT NULL,"
        "entity_id TEXT NOT NULL, user_email TEXT NOT NULL, user_type TEXT NOT NULL,"
        "timestamp TEXT NOT NULL, details TEXT NOT NULL DEFAULT '');"
    )

    c.execute('SELECT COUNT(*) FROM categories')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO categories (slug,name,icon,description) VALUES (?,?,?,?)', [
            ('pain',         'Pain Relief',     '💊', 'Analgesics, antipyretics, NSAIDs'),
            ('antibiotics',  'Antibiotics',      '🦠', 'Prescription antibacterial medications'),
            ('vitamins',     'Vitamins & Supps', '💉', 'Daily vitamins, minerals, supplements'),
            ('skincare',     'Skin Care',        '🧴', 'Dermatological products and treatments'),
            ('babycare',     'Baby Care',        '🍼', 'Pediatric medications and baby products'),
            ('personalcare', 'Personal Hygiene', '🧼', 'Sanitizers, hand wash, hygiene products'),
        ])

    c.execute('SELECT COUNT(*) FROM admins WHERE is_master=1')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO admins (name,email,phone,password_hash,role,is_master,created_at) VALUES (?,?,?,?,?,?,?)',
                  ('Master Administrator','master@medicart.com','+91 99000 00000',hash_pw('master123'),'Master Admin',1,datetime.now().isoformat()))
    c.execute('SELECT COUNT(*) FROM admins WHERE is_master=0')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO admins (name,email,phone,password_hash,role,is_master,created_at) VALUES (?,?,?,?,?,?,?)',
                  ('Dr. Kavya Suresh','admin@medicart.com','+91 98450 99887',hash_pw('admin123'),'Head Pharmacist',0,datetime.now().isoformat()))
    c.execute('SELECT COUNT(*) FROM users')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO users (name,email,phone,password_hash,address,created_at) VALUES (?,?,?,?,?,?)',
                  ('John Doe','john@example.com','+91 98765 43210',hash_pw('password123'),'44, Lotus Residency, MG Road, Kochi, Kerala 682016',datetime.now().isoformat()))
    c.execute('SELECT COUNT(*) FROM medicines')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO medicines (name,category_id,price,rating,reviews,stock,rx_required,manufacturer,description) VALUES (?,?,?,?,?,?,?,?,?)', [
            ('Paracetamol 500mg',             1,  45.0, 4.8, 120, 240, 0, 'Apex Health',      'Relieves mild to moderate pain including headache, toothache, and fever.'),
            ('Amoxicillin 250mg',             2, 120.0, 4.6,  88,  60, 1, 'Sun Pharma',       'Broad-spectrum antibiotic for bacterial infections.'),
            ('Vitamin C 1000mg Effervescent', 3, 180.0, 4.9, 210, 150, 0, 'Redoxon Labs',     'Immune support tablets enriched with Zinc and Antioxidants.'),
            ('Soothing Aloe Vera Gel 200ml',  4, 210.0, 4.5,  64,  90, 0, 'Nature Care',      'Hydrating cooling gel for sunburns and dry skin.'),
            ('Baby Colic Relief Drops',       5, 160.0, 4.4,  52,  40, 0, 'Himalaya Baby',    'Natural drops to relieve infantile colic and gas.'),
            ('Antibacterial Hand Wash 250ml', 6,  95.0, 4.3,  73, 200, 0, 'Dettol Herbal',    'Enriched with Neem & Tulsi, eliminates 99.9% germs.'),
            ('Ibuprofen 400mg',               1,  60.0, 4.7,  98,  12, 0, 'Abbott Healthcare','Fast-acting anti-inflammatory for joint pain and fever.'),
            ('Azithromycin 500mg (3 Tabs)',   2, 150.0, 4.5,  41,   0, 1, 'Cipla Ltd',        'Macrolide antibiotic for respiratory infections.'),
            ('Adult Multivitamin Gummies',    3, 220.0, 4.8, 134,  75, 0, 'NutraLife',        'Fruit-flavored gummies with B-complex, D3, and Iron.'),
            ('Zinc Oxide Diaper Rash Cream',  5, 140.0, 4.6,  59,  55, 0, 'Sebamed Baby',     'Protective barrier cream for delicate baby skin.'),
        ])
    c.execute('SELECT COUNT(*) FROM suppliers')
    if c.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        c.executemany('INSERT INTO suppliers (name,contact_person,phone,email,categories,address,created_at) VALUES (?,?,?,?,?,?,?)', [
            ('MedSupply Co.',         'Suresh Nair', '+91 98450 11223','suresh@medsupply.in',   'Pain Relief, Antibiotics',  'Ernakulam, Kerala',         now),
            ('Wellness Distributors', 'Priya Menon', '+91 97460 22110','priya@wellnessdist.in', 'Vitamins, Personal Hygiene','Kozhikode, Kerala',         now),
            ('BabyCare Traders',      'Arun Das',    '+91 94470 33987','arun@babycaretraders.in','Baby Care, Skin Care',     'Thiruvananthapuram, Kerala', now),
        ])
    c.execute('SELECT COUNT(*) FROM stock_batches')
    if c.fetchone()[0] == 0:
        today = datetime.now().strftime('%Y-%m-%d')
        c.executemany('INSERT INTO stock_batches (medicine_id,batch_no,quantity,expiry_date,status,received_date,supplier_id) VALUES (?,?,?,?,?,?,?)', [
            (1,'B1042',240,'2027-11-15','ok',      today,1),
            (2,'B2210', 60,'2026-10-20','low',     today,1),
            (7,'B3305', 12,'2026-09-18','expiring',today,1),
            (8,'B4471',  0,'2026-10-02','out',     today,1),
            (3,'B5120',150,'2027-02-18','ok',      today,2),
        ])
    c.execute('SELECT COUNT(*) FROM orders')
    if c.fetchone()[0] == 0:
        now = datetime.now().isoformat()
        c.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)',
                  ('ORD-1042','john@example.com','2026-08-20',270.0,'Delivered','John Doe','44, Lotus Residency, Kochi','+91 98765 43210',now))
        c.executemany('INSERT INTO order_items (order_id,medicine_id,quantity,unit_price) VALUES (?,?,?,?)',
                      [('ORD-1042',1,2,45.0),('ORD-1042',3,1,180.0)])
        c.execute('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)',
                  ('ORD-1088','john@example.com','2026-08-28',315.0,'Shipped','John Doe','44, Lotus Residency, Kochi','+91 98765 43210',now))
        c.executemany('INSERT INTO order_items (order_id,medicine_id,quantity,unit_price) VALUES (?,?,?,?)',
                      [('ORD-1088',6,1,95.0),('ORD-1088',9,1,220.0)])
    c.execute('SELECT COUNT(*) FROM prescriptions')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO prescriptions (filename,patient_name,doctor_name,date,status,order_id,user_email) VALUES (?,?,?,?,?,?,?)',
                  ('prescription_aug.pdf','John Doe','Dr. Kavya Suresh','2026-08-25','Verified','ORD-1042','john@example.com'))
    conn.commit()
    conn.close()

class PharmacyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        n = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,DELETE,PATCH,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip('/')
        if path in ('', '/'):
            self.send_html(get_html()); return
        conn = get_db(); c = conn.cursor()
        try:
            if path == '/api/categories':
                c.execute('SELECT * FROM categories ORDER BY id ASC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/medicines':
                c.execute('SELECT m.*,cat.slug as cat,cat.name as cat_name,cat.icon as cat_icon '
                          'FROM medicines m JOIN categories cat ON m.category_id=cat.id ORDER BY m.category_id ASC, m.id ASC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif re.match(r'^/api/medicines/(\d+)$', path):
                mid = int(path.split('/')[-1])
                c.execute('SELECT m.*,cat.slug as cat,cat.name as cat_name '
                          'FROM medicines m JOIN categories cat ON m.category_id=cat.id WHERE m.id=?', (mid,))
                row = c.fetchone()
                self.send_json(dict(row) if row else {}, 200 if row else 404)
            elif path == '/api/suppliers':
                c.execute('SELECT * FROM suppliers ORDER BY id ASC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/orders':
                c.execute('SELECT * FROM orders ORDER BY date DESC, id DESC')
                result = []
                for o in c.fetchall():
                    d = dict(o)
                    c.execute('SELECT oi.*,m.name as medicine_name FROM order_items oi '
                              'JOIN medicines m ON oi.medicine_id=m.id WHERE oi.order_id=? ORDER BY oi.id ASC', (d['id'],))
                    d['items'] = [dict(i) for i in c.fetchall()]
                    result.append(d)
                self.send_json(result)
            elif path == '/api/prescriptions':
                c.execute('SELECT * FROM prescriptions ORDER BY date DESC, id DESC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/admin/stock':
                c.execute('SELECT sb.*,m.name as medicine_name,cat.name as category_name '
                          'FROM stock_batches sb '
                          'JOIN medicines m ON sb.medicine_id=m.id '
                          'JOIN categories cat ON m.category_id=cat.id '
                          'ORDER BY sb.expiry_date ASC, sb.quantity ASC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/users':
                c.execute('SELECT id,name,email,phone,address,created_at FROM users ORDER BY id ASC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/admins':
                c.execute('SELECT id,name,email,phone,role,is_master,created_at FROM admins ORDER BY is_master DESC, id ASC')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/audit':
                c.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT 200')
                self.send_json([dict(r) for r in c.fetchall()])
            elif path == '/api/db/views':
                c.execute('SELECT * FROM v_sales_by_category')
                v_sales = [dict(r) for r in c.fetchall()]
                c.execute('SELECT * FROM v_stock_alerts')
                v_alerts = [dict(r) for r in c.fetchall()]
                c.execute('SELECT * FROM v_customer_summary')
                v_cust = [dict(r) for r in c.fetchall()]
                self.send_json({'sales_by_category': v_sales, 'stock_alerts': v_alerts, 'customer_summary': v_cust})
            elif path == '/api/reports/sales':
                c.execute('SELECT COUNT(*) as total_orders,COALESCE(SUM(total),0) as total_revenue FROM orders')
                summary = dict(c.fetchone())
                c.execute('SELECT COUNT(*) FROM users')
                summary['total_customers'] = c.fetchone()[0]
                c.execute('SELECT COUNT(*) FROM medicines')
                summary['total_medicines'] = c.fetchone()[0]
                c.execute('SELECT status,COUNT(*) as cnt FROM orders GROUP BY status')
                summary['by_status'] = [dict(r) for r in c.fetchall()]
                c.execute('SELECT cat.name,cat.icon,'
                          'COALESCE(SUM(oi.quantity*oi.unit_price),0) as revenue,'
                          'COALESCE(SUM(oi.quantity),0) as units '
                          'FROM categories cat '
                          'LEFT JOIN medicines m ON m.category_id=cat.id '
                          'LEFT JOIN order_items oi ON oi.medicine_id=m.id '
                          'GROUP BY cat.id ORDER BY revenue DESC')
                summary['by_category'] = [dict(r) for r in c.fetchall()]
                c.execute('SELECT m.name,COALESCE(SUM(oi.quantity),0) as units_sold,'
                          'COALESCE(SUM(oi.quantity*oi.unit_price),0) as revenue '
                          'FROM medicines m LEFT JOIN order_items oi ON oi.medicine_id=m.id '
                          'GROUP BY m.id ORDER BY units_sold DESC LIMIT 5')
                summary['top_medicines'] = [dict(r) for r in c.fetchall()]
                self.send_json(summary)
            elif path == '/api/reports/stock':
                c.execute('SELECT sb.*,m.name as medicine_name FROM stock_batches sb '
                          'JOIN medicines m ON sb.medicine_id=m.id '
                          "WHERE sb.status!='ok' ORDER BY sb.quantity ASC")
                alerts = [dict(r) for r in c.fetchall()]
                c.execute('SELECT sb.*,m.name as medicine_name FROM stock_batches sb '
                          'JOIN medicines m ON sb.medicine_id=m.id ORDER BY sb.expiry_date ASC')
                self.send_json({'alerts': alerts, 'all_stock': [dict(r) for r in c.fetchall()]})
            else:
                self.send_json({'error': 'Not found'}, 404)
        finally:
            conn.close()

    def do_POST(self):
        path = urlparse(self.path).path.rstrip('/')
        body = self.read_body()
        conn = get_db(); c = conn.cursor()
        try:
            if path == '/api/auth/login':
                email = body.get('email','').strip(); pw = body.get('password','').strip()
                ltype = body.get('type','auto')
                user = None; utype = None
                if ltype in ('admin','auto'):
                    c.execute('SELECT * FROM admins WHERE email=?',(email,))
                    row = c.fetchone()
                    if row and check_pw(pw, row['password_hash']):
                        user = dict(row); utype = 'admin'
                if not user and ltype in ('user','auto'):
                    c.execute('SELECT * FROM users WHERE email=?',(email,))
                    row = c.fetchone()
                    if row and check_pw(pw, row['password_hash']):
                        user = dict(row); utype = 'user'
                # Fallback across tables in case user selected wrong type in dropdown
                if not user:
                    c.execute('SELECT * FROM users WHERE email=?',(email,))
                    row = c.fetchone()
                    if row and check_pw(pw, row['password_hash']):
                        user = dict(row); utype = 'user'
                if not user:
                    c.execute('SELECT * FROM admins WHERE email=?',(email,))
                    row = c.fetchone()
                    if row and check_pw(pw, row['password_hash']):
                        user = dict(row); utype = 'admin'
                if user:
                    user.pop('password_hash', None)
                    audit(conn,'LOGIN',utype,user.get('id','?'),email,utype,'Login')
                    self.send_json({'success':True,'user':user,'type':utype})
                else:
                    self.send_json({'success':False,'message':'Invalid email or password'},401)
            elif path == '/api/auth/signup':
                name=body.get('name','').strip(); email=body.get('email','').strip()
                phone=body.get('phone','').strip(); pw=body.get('password','').strip()
                if not name or not email or not pw:
                    self.send_json({'success':False,'message':'Name, email and password required'},400); return
                c.execute('SELECT id FROM users WHERE email=?',(email,))
                if c.fetchone():
                    self.send_json({'success':False,'message':'Email already registered. Please sign in.'},409); return
                c.execute('INSERT INTO users (name,email,phone,password_hash,address,created_at) VALUES (?,?,?,?,?,?)',
                          (name,email,phone,hash_pw(pw),'',datetime.now().isoformat()))
                conn.commit()
                uid = c.lastrowid
                audit(conn,'SIGNUP','users',uid,email,'user','New customer: '+name)
                new_user = {'id': uid, 'name': name, 'email': email, 'phone': phone, 'address': '', 'is_master': 0}
                self.send_json({'success':True,'user':new_user,'type':'user'})
            elif path == '/api/auth/create-admin':
                name=body.get('name','').strip(); email=body.get('email','').strip()
                phone=body.get('phone','').strip(); pw=body.get('password','').strip()
                role=body.get('role','Pharmacist').strip(); by=body.get('by_email','master@medicart.com')
                if not name or not email or not pw:
                    self.send_json({'success':False,'message':'Name, email and password required'},400); return
                c.execute('SELECT id FROM admins WHERE email=?',(email,))
                if c.fetchone():
                    self.send_json({'success':False,'message':'Admin email already exists'},409); return
                c.execute('INSERT INTO admins (name,email,phone,password_hash,role,is_master,created_at) VALUES (?,?,?,?,?,?,?)',
                          (name,email,phone,hash_pw(pw),role,0,datetime.now().isoformat()))
                conn.commit()
                audit(conn,'CREATE_ADMIN','admins',c.lastrowid,by,'master','Created: '+name+' ('+role+')')
                self.send_json({'success':True})
            elif path == '/api/orders':
                oid=body.get('id','ORD-'+str(int(datetime.now().timestamp())))
                uemail=body.get('user_email','guest@medicart.com')
                total=float(body.get('total',0)); items=body.get('items',[])
                c.execute('INSERT OR REPLACE INTO orders (id,user_email,date,total,status,delivery_name,delivery_address,delivery_phone,created_at) VALUES (?,?,?,?,?,?,?,?,?)',
                          (oid,uemail,body.get('date',datetime.now().strftime('%Y-%m-%d')),total,'Placed',
                           body.get('delivery_name',''),body.get('delivery_address',''),
                           body.get('delivery_phone',''),datetime.now().isoformat()))
                for it in items:
                    c.execute('INSERT INTO order_items (order_id,medicine_id,quantity,unit_price) VALUES (?,?,?,?)',
                              (oid,it.get('id',0),it.get('qty',1),it.get('price',0)))
                conn.commit()
                audit(conn,'PLACE_ORDER','orders',oid,uemail,'user','Total: Rs.'+str(total))
                self.send_json({'success':True,'id':oid})
            elif path == '/api/prescriptions':
                c.execute('INSERT INTO prescriptions (filename,patient_name,doctor_name,date,status,order_id,user_email) VALUES (?,?,?,?,?,?,?)',
                          (body.get('file','rx.pdf'),body.get('patient',''),body.get('doctor',''),
                           body.get('date',datetime.now().strftime('%Y-%m-%d')),'Pending',
                           body.get('order_id',''),body.get('user_email','')))
                conn.commit()
                audit(conn,'SUBMIT_RX','prescriptions',c.lastrowid,body.get('user_email','guest'),'user',body.get('patient',''))
                self.send_json({'success':True})
            elif path == '/api/suppliers':
                c.execute('INSERT INTO suppliers (name,contact_person,phone,email,categories,address,created_at) VALUES (?,?,?,?,?,?,?)',
                          (body.get('name',''),body.get('contact',''),body.get('phone',''),
                           body.get('email',''),body.get('cats',''),body.get('address',''),datetime.now().isoformat()))
                conn.commit()
                sid=c.lastrowid
                audit(conn,'ADD_SUPPLIER','suppliers',sid,body.get('by_email','admin'),'admin',body.get('name',''))
                self.send_json({'success':True,'id':sid})
            elif path == '/api/medicines':
                name=body.get('name','').strip(); mfr=body.get('manufacturer','').strip()
                if not name or not mfr:
                    self.send_json({'success':False,'message':'Name and manufacturer required'},400); return
                c.execute('INSERT INTO medicines (name,category_id,price,rating,reviews,stock,rx_required,manufacturer,description) VALUES (?,?,?,?,?,?,?,?,?)',
                          (name,int(body.get('category_id',1)),float(body.get('price',0)),
                           4.5,0,int(body.get('stock',0)),int(body.get('rx',0)),mfr,body.get('description','')))
                conn.commit(); mid=c.lastrowid
                audit(conn,'ADD_MEDICINE','medicines',mid,body.get('by_email','admin'),'admin','Added: '+name)
                self.send_json({'success':True,'id':mid})
            else:
                self.send_json({'error':'Not found'},404)
        finally:
            conn.close()

    def do_PATCH(self):
        path = urlparse(self.path).path.rstrip('/')
        body = self.read_body(); conn = get_db(); c = conn.cursor()
        try:
            m = re.match(r'^/api/orders/([^/]+)/status$', path)
            if m:
                oid=m.group(1); ns=body.get('status','')
                if ns not in ('Placed','Confirmed','Shipped','Delivered','Cancelled'):
                    self.send_json({'success':False,'message':'Invalid status'},400); return
                c.execute('UPDATE orders SET status=? WHERE id=?',(ns,oid)); conn.commit()
                audit(conn,'UPDATE_STATUS','orders',oid,body.get('by_email','admin'),'admin','Status: '+ns)
                self.send_json({'success':True})
            else:
                self.send_json({'error':'Not found'},404)
        finally:
            conn.close()

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip('/')
        body = self.read_body(); conn = get_db(); c = conn.cursor()
        try:
            ms = re.match(r'^/api/suppliers/(\d+)$', path)
            mm = re.match(r'^/api/medicines/(\d+)$', path)
            if ms:
                sid=int(ms.group(1))
                c.execute('SELECT name FROM suppliers WHERE id=?',(sid,))
                row=c.fetchone()
                if not row: self.send_json({'error':'Not found'},404); return
                c.execute('DELETE FROM suppliers WHERE id=?',(sid,)); conn.commit()
                audit(conn,'DELETE_SUPPLIER','suppliers',sid,body.get('by_email','admin'),'admin',row['name'])
                self.send_json({'success':True})
            elif mm:
                mid=int(mm.group(1))
                c.execute('SELECT name FROM medicines WHERE id=?',(mid,))
                row=c.fetchone()
                if not row: self.send_json({'error':'Not found'},404); return
                c.execute('DELETE FROM order_items WHERE medicine_id=?',(mid,))
                c.execute('DELETE FROM stock_batches WHERE medicine_id=?',(mid,))
                c.execute('DELETE FROM medicines WHERE id=?',(mid,)); conn.commit()
                audit(conn,'DELETE_MEDICINE','medicines',mid,body.get('by_email','admin'),'admin',row['name'])
                self.send_json({'success':True})
            else:
                self.send_json({'error':'Not found'},404)
        finally:
            conn.close()

HTML = "<!DOCTYPE html><html lang='en' data-theme='light'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1.0'><title>MediCart Pharmacy | DBMS Project</title><link href='https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@300;400;500;600;700&display=swap' rel='stylesheet'><style>:root{--p9:#082F24;--p7:#0E8A5A;--p6:#129966;--p1:#D1FAE5;--p0:#EAF6F0;--t1:#0F172A;--t2:#334155;--t3:#64748B;--bg:#fff;--sfbg:#F8FAFC;--cbg:#fff;--bd:#E2E8F0;--a6:#D97706;--a0:#FFFBEB;--r6:#DC2626;--r0:#FEF2F2;--pu:#5B21B6;--pu0:#F5F3FF;--tr:all .2s ease}[data-theme=dark]{--t1:#F8FAFC;--t2:#CBD5E1;--t3:#94A3B8;--bg:#0B1310;--sfbg:#111C18;--cbg:#16241F;--bd:#23362E;--p0:#162E25}*{box-sizing:border-box;margin:0;padding:0}html,body{font-family:'Inter',sans-serif;color:var(--t1);background:var(--bg);line-height:1.5}h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif}a{color:inherit;text-decoration:none}button{font-family:inherit;cursor:pointer;border:none;background:none}input,select,textarea{font-family:inherit;font-size:14px;color:var(--t1)}.page{display:none}.page.active{display:block;animation:fi .25s ease-out}@keyframes fi{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}.wrap{max-width:1280px;margin:0 auto;padding:0 5vw}.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border-radius:8px;padding:10px 20px;font-weight:600;font-size:14px;border:1px solid transparent;transition:var(--tr)}.btn-primary{background:var(--p7);color:#fff}.btn-primary:hover{background:var(--p6)}.btn-secondary{background:var(--p0);color:var(--p7);border-color:var(--p1)}.btn-outline{background:transparent;border-color:var(--p7);color:var(--p7)}.btn-outline:hover{background:var(--p0)}.btn-ghost{background:transparent;color:var(--t3);border-color:var(--bd)}.btn-ghost:hover{background:var(--sfbg)}.btn-danger{background:transparent;color:var(--r6);border-color:var(--r6)}.btn-danger:hover{background:var(--r0)}.btn-purple{background:var(--pu);color:#fff}.btn-sm{padding:5px 13px;font-size:13px}.btn-block{width:100%}.card{border:1px solid var(--bd);border-radius:12px;padding:24px;background:var(--cbg)}.muted{color:var(--t3)}.small{font-size:13px}.mono{font-family:monospace;font-size:12px}.divider{height:1px;background:var(--bd);margin:20px 0}.badge{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:700;padding:3px 9px;border-radius:999px;white-space:nowrap}.bg{background:var(--p0);color:var(--p7);border:1px solid var(--p1)}.ba{background:var(--a0);color:var(--a6);border:1px solid #FDE68A}.br{background:var(--r0);color:var(--r6);border:1px solid #FECACA}.bp{background:var(--pu0);color:var(--pu);border:1px solid #DDD6FE}.field{display:flex;flex-direction:column;gap:5px;margin-bottom:14px}.field label{font-size:13px;font-weight:600;color:var(--t2)}.field input,.field select,.field textarea{border:1px solid var(--bd);border-radius:8px;padding:9px 13px;background:var(--cbg);outline:none;transition:border-color .15s}.field input:focus,.field select:focus,.field textarea:focus{border-color:var(--p7)}.nav{position:sticky;top:0;z-index:100;background:var(--cbg);border-bottom:1px solid var(--bd);backdrop-filter:blur(14px)}.nw{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 5vw;height:66px}.brand{display:flex;align-items:center;gap:10px;font-family:'Space Grotesk';font-weight:700;font-size:19px;cursor:pointer}.bmark{width:34px;height:34px;border-radius:9px;background:var(--p7);display:flex;align-items:center;justify-content:center;color:#fff}.nl{display:flex;align-items:center;gap:20px}.nl a{font-size:14px;font-weight:500;color:var(--t2);padding:7px 0;border-bottom:2px solid transparent;cursor:pointer;transition:var(--tr)}.nl a:hover{color:var(--p7);border-color:var(--p7)}.nr{display:flex;align-items:center;gap:10px}.sbox{display:flex;align-items:center;gap:7px;border:1px solid var(--bd);border-radius:8px;padding:7px 11px;background:var(--sfbg);width:200px}.sbox input{border:none;outline:none;background:transparent;flex:1;font-size:13px}.iBtn{position:relative;width:38px;height:38px;border-radius:8px;border:1px solid var(--bd);background:var(--cbg);display:flex;align-items:center;justify-content:center;color:var(--t2)}.cbadge{position:absolute;top:-5px;right:-5px;background:var(--r6);color:#fff;font-size:10px;font-weight:700;min-width:17px;height:17px;border-radius:999px;display:flex;align-items:center;justify-content:center}.hero{display:grid;grid-template-columns:1.1fr 0.9fr;gap:48px;padding:56px 5vw;background:linear-gradient(135deg,var(--p0),var(--sfbg));align-items:center;border-bottom:1px solid var(--bd)}.hero h1{font-size:clamp(2rem,4vw,3.2rem);line-height:1.1;margin-bottom:16px}.hero h1 span{color:var(--p7)}.hero p{font-size:16px;color:var(--t3);max-width:46ch;margin-bottom:24px}.trust-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px;padding:28px 5vw;border-bottom:1px solid var(--bd);background:var(--cbg)}.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;padding:32px 5vw;text-align:center;border-bottom:1px solid var(--bd)}.stats-grid b{display:block;font-family:'Space Grotesk';font-size:30px;color:var(--p7)}.cat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin:18px 0 40px}.cat-card{border:1px solid var(--bd);border-radius:12px;padding:20px 12px;text-align:center;background:var(--cbg);cursor:pointer;transition:var(--tr)}.cat-card:hover{border-color:var(--p7);background:var(--p0)}.cat-card .icon{font-size:28px;margin-bottom:8px}.ml{display:grid;grid-template-columns:240px 1fr;gap:28px;padding:28px 5vw 56px;align-items:start}.mtb{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;flex-wrap:wrap;gap:10px}.mg{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:18px}.mc{border:1px solid var(--bd);border-radius:12px;padding:16px;background:var(--cbg);display:flex;flex-direction:column;gap:10px}.dl{display:grid;grid-template-columns:260px 1fr 260px;gap:28px;padding:20px 5vw 40px;align-items:start}.dimg{width:100%;aspect-ratio:1;border-radius:12px;background:var(--p0);border:1px solid var(--bd);display:flex;align-items:center;justify-content:center;font-size:64px}.dropzone{border:2px dashed var(--p6);border-radius:12px;padding:32px 18px;text-align:center;background:var(--p0);cursor:pointer}.two{display:grid;grid-template-columns:1.4fr 1fr;gap:28px;padding:28px 5vw 56px;align-items:start}table{width:100%;border-collapse:collapse;text-align:left}th{font-size:11px;font-weight:700;text-transform:uppercase;color:var(--t3);padding:11px 14px;border-bottom:1px solid var(--bd);background:var(--sfbg)}td{padding:12px 14px;border-bottom:1px solid var(--bd);font-size:14px;vertical-align:middle}.sl{display:flex;justify-content:space-between;padding:9px 0;font-size:14px}.sl.tot{font-weight:700;font-size:17px;border-top:1px solid var(--bd);margin-top:6px;padding-top:14px}.tracker{display:flex;align-items:flex-start;justify-content:space-between;padding:20px 6px;position:relative}.ts{flex:1;text-align:center;position:relative;z-index:2}.dot{width:22px;height:22px;border-radius:50%;border:2px solid var(--bd);background:var(--cbg);margin:0 auto 6px;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700}.tline{position:absolute;top:11px;left:-50%;width:100%;height:3px;background:var(--bd);z-index:-1}.ts:first-child .tline{display:none}.ts.done .dot{background:var(--p7);border-color:var(--p7);color:#fff}.ts.done .tline{background:var(--p7)}.krow{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:18px;padding:28px 5vw 14px}.kpi{border:1px solid var(--bd);border-radius:12px;padding:18px 20px;background:var(--cbg)}.kpi .lbl{font-size:13px;color:var(--t3);font-weight:500}.kpi .val{font-family:'Space Grotesk';font-size:26px;font-weight:700;margin-top:4px}.kpi .sub{font-size:12px;color:var(--t3);margin-top:2px}.aw{display:flex;justify-content:center;padding:56px 5vw}.ab{width:100%;max-width:430px;border:1px solid var(--bd);border-radius:12px;padding:32px;background:var(--cbg);box-shadow:0 4px 20px rgba(0,0,0,.06)}.atabs{display:flex;border:1px solid var(--bd);border-radius:8px;overflow:hidden;margin-bottom:20px}.atab{flex:1;padding:9px;border:none;background:var(--sfbg);font-weight:600;font-size:14px;color:var(--t3);cursor:pointer}.atab.active{background:var(--p7);color:#fff}.chart-wrap{display:flex;align-items:flex-end;gap:8px;height:160px;padding:0 4px;margin:16px 0}.bar-col{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;height:100%;gap:5px}.bar{width:65%;background:linear-gradient(to top,var(--p7),var(--p6));border-radius:6px 6px 0 0;min-height:4px;transition:height .4s ease}.bar-val{font-size:10px;font-weight:700;color:var(--p7);white-space:nowrap}.bar-lbl{font-size:10px;color:var(--t3);text-align:center;max-width:70px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mpanel{border:1.5px solid var(--pu);border-radius:12px;padding:20px;background:var(--pu0);margin-bottom:20px}.ph{padding:36px 5vw 8px}.bc{padding:18px 5vw 0;font-size:13px;color:var(--t3)}.sbadge{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:600;padding:4px 10px;border-radius:999px;background:#EDE9FE;color:#5B21B6;border:1px solid #DDD6FE}.footer{background:var(--p9);color:#D1FAE5;padding:56px 5vw 24px;margin-top:56px}.fg{display:grid;grid-template-columns:1.5fr 1fr 1fr 1fr;gap:36px;margin-bottom:36px}.footer h4{color:#fff;font-size:14px;margin-bottom:14px}.footer p,.footer a{font-size:13px;color:#A7F3D0;display:block;margin-bottom:8px}.fbot{border-top:1px solid rgba(255,255,255,.1);padding-top:20px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;font-size:12px;color:#6EE7B7}#toast{position:fixed;bottom:22px;right:22px;background:var(--p9);color:#fff;padding:13px 20px;border-radius:10px;font-size:13px;opacity:0;transform:translateY(16px);pointer-events:none;transition:all .3s;z-index:999;display:flex;align-items:center;gap:8px}#toast.show{opacity:1;transform:translateY(0)}@media(max-width:1024px){.hero,.dl,.two{grid-template-columns:1fr}.stats-grid,.fg{grid-template-columns:1fr 1fr}}@media(max-width:768px){.ml{grid-template-columns:1fr}.nl{display:none}.stats-grid{grid-template-columns:1fr 1fr}}</style></head><body><div id='toast'><span>&#10003;</span><span id='tmsg'></span></div><header class='nav' id='cNav'><div class='nw'><a class='brand' data-page='home'><span class='bmark'><svg viewBox='0 0 24 24' width='16' height='16' stroke='#fff' fill='none' stroke-width='2.5'><path d='M12 3v18M3 12h18'/></svg></span>MediCart</a><div class='nl'><a data-page='home'>Home</a><a data-page='medicines'>Medicines</a><a data-page='prescriptions'>Prescriptions</a><a data-page='orders'>Orders</a><a data-page='profile'>Profile</a><a data-page='about'>About</a><a data-page='contact'>Contact</a></div><div class='nr'><div class='sbox'><svg viewBox='0 0 24 24' width='14' height='14' stroke='var(--t3)' fill='none' stroke-width='2'><circle cx='11' cy='11' r='7'/><path d='M21 21l-4-4'/></svg><input id='si' placeholder='Search...' autocomplete='off'></div><button class='iBtn' id='tgl'><svg viewBox='0 0 24 24' width='15' height='15' stroke='currentColor' fill='none' stroke-width='2'><circle cx='12' cy='12' r='5'/><path d='M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42'/></svg></button><button class='iBtn' data-page='cart'><svg viewBox='0 0 24 24' width='15' height='15' stroke='currentColor' fill='none' stroke-width='2'><circle cx='9' cy='21' r='1'/><circle cx='19' cy='21' r='1'/><path d='M1 1h4l2.6 13.4a2 2 0 0 0 2 1.6h9.4a2 2 0 0 0 2-1.6L23 6H6'/></svg><span class='cbadge' id='cc'>0</span></button><button class='btn btn-outline btn-sm' id='accBtn' data-page='login'>Login</button><button class='btn btn-ghost btn-sm' data-page='admin'>Admin Portal</button></div></div></header><header class='nav' id='aNav' style='display:none;background:var(--p9)'><div class='nw'><a class='brand' data-page='admin' style='color:#fff'><span class='bmark' style='background:#fff'><svg viewBox='0 0 24 24' width='16' height='16' stroke='#082F24' fill='none' stroke-width='2.5'><path d='M12 3v18M3 12h18'/></svg></span>MediCart Admin</a><div class='nl'><a data-page='admin' style='color:#A7F3D0'>Dashboard</a><a data-page='medmgmt' style='color:#A7F3D0'>Medicines</a><a data-page='suppliers' style='color:#A7F3D0'>Suppliers</a><a data-page='prescriptions' style='color:#A7F3D0'>Rx Queue</a><a data-page='orders' style='color:#A7F3D0'>Orders</a><a data-page='reports' style='color:#A7F3D0'>Reports</a><a data-page='audit' id='auditLink' style='color:#C4B5FD;display:none'>&#128081; Audit Log</a></div><div class='nr'><span class='badge bp' id='aBadge'>Admin</span><button class='btn btn-secondary btn-sm' data-page='home'>Exit Store</button></div></div></header><main><section class='page active' id='page-home'><div class='hero'><div><span class='badge bg' style='margin-bottom:14px;font-size:12px;padding:4px 12px;font-weight:600'>Licensed Healthcare Partner</span><h1 style='font-size:clamp(2.2rem,4vw,3.4rem);line-height:1.1;margin-bottom:18px'>Your health, <span style='color:var(--p7)'>our priority.</span></h1><p style='font-size:16px;color:var(--t3);max-width:48ch;margin-bottom:28px;line-height:1.6'>Order 100% genuine medicines online, upload prescriptions effortlessly for fast verification, and enjoy instant home delivery.</p><div style='display:flex;gap:14px;flex-wrap:wrap'><button class='btn btn-primary' data-page='medicines' style='padding:12px 24px;font-size:15px'>Order Medicines Now &rarr;</button><button class='btn btn-outline' data-page='prescriptions' style='padding:12px 24px;font-size:15px'>Upload Prescription</button></div></div><svg class='hero-graphic' viewBox='0 0 400 320' fill='none' style='width:100%;max-width:380px;height:auto;filter:drop-shadow(0 10px 20px rgba(14,138,90,0.12));margin:0 auto;display:block'><rect x='120' y='50' width='160' height='220' rx='16' fill='var(--cbg)' stroke='var(--p7)' stroke-width='2.5'/><rect x='150' y='25' width='100' height='40' rx='8' fill='var(--p7)'/><line x1='200' y1='35' x2='200' y2='55' stroke='#fff' stroke-width='4' stroke-linecap='round'/><line x1='190' y1='45' x2='210' y2='45' stroke='#fff' stroke-width='4' stroke-linecap='round'/><circle cx='170' cy='120' r='16' fill='var(--p0)' stroke='var(--p6)' stroke-width='2'/><circle cx='230' cy='120' r='16' fill='var(--a0)' stroke='var(--a6)' stroke-width='2'/><rect x='155' y='160' width='90' height='12' rx='4' fill='var(--p1)'/><rect x='155' y='180' width='60' height='12' rx='4' fill='var(--bd)'/><path d='M60 260 C 100 240, 140 280, 180 260' stroke='var(--p6)' stroke-width='4' stroke-dasharray='6 6'/><circle cx='60' cy='260' r='8' fill='var(--p7)'/><circle cx='340' cy='100' r='28' fill='var(--p0)'/><path d='M330 100 L338 108 L352 92' stroke='var(--p7)' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'/></svg></div><div class='trust-grid' style='display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;padding:28px 5vw;border-bottom:1px solid var(--bd);background:var(--cbg)'><div style='display:flex;align-items:center;gap:14px'><div style='width:40px;height:40px;border-radius:10px;background:var(--p0);display:flex;align-items:center;justify-content:center;color:var(--p7);flex-shrink:0'><svg viewBox='0 0 24 24' width='20' height='20' stroke='currentColor' fill='none' stroke-width='2'><path d='M12 2l8 4v6c0 5-3.5 8-8 10-4.5-2-8-5-8-10V6l8-4z'/></svg></div><div><h4 style='font-size:14px;font-weight:700'>Genuine Medicines</h4><p class='muted small' style='margin-top:2px'>100% original verified products direct from licensed manufacturers.</p></div></div><div style='display:flex;align-items:center;gap:14px'><div style='width:40px;height:40px;border-radius:10px;background:var(--p0);display:flex;align-items:center;justify-content:center;color:var(--p7);flex-shrink:0'><svg viewBox='0 0 24 24' width='20' height='20' stroke='currentColor' fill='none' stroke-width='2'><path d='M13 2L3 14h9l-1 8 10-12h-9l1-8z'/></svg></div><div><h4 style='font-size:14px;font-weight:700'>Express Delivery</h4><p class='muted small' style='margin-top:2px'>Get doorstep delivery within 2 hours in selected city locations.</p></div></div><div style='display:flex;align-items:center;gap:14px'><div style='width:40px;height:40px;border-radius:10px;background:var(--p0);display:flex;align-items:center;justify-content:center;color:var(--p7);flex-shrink:0'><svg viewBox='0 0 24 24' width='20' height='20' stroke='currentColor' fill='none' stroke-width='2'><path d='M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z'/><path d='M9 12l2 2 4-4'/></svg></div><div><h4 style='font-size:14px;font-weight:700'>Pharmacist Verified</h4><p class='muted small' style='margin-top:2px'>Every order and prescription double-checked by qualified experts.</p></div></div><div style='display:flex;align-items:center;gap:14px'><div style='width:40px;height:40px;border-radius:10px;background:var(--p0);display:flex;align-items:center;justify-content:center;color:var(--p7);flex-shrink:0'><svg viewBox='0 0 24 24' width='20' height='20' stroke='currentColor' fill='none' stroke-width='2'><circle cx='12' cy='12' r='10'/><polyline points='12 6 12 12 16 14'/></svg></div><div><h4 style='font-size:14px;font-weight:700'>24/7 Support</h4><p class='muted small' style='margin-top:2px'>Round-the-clock medical consultation and customer service support.</p></div></div></div><div class='stats-grid' style='background:var(--sfbg)'><div><b>10</b><span>DB Tables (3NF)</span></div><div><b>15+</b><span>API Routes</span></div><div><b>0</b><span>External Dependencies</span></div><div><b>3</b><span>Role Levels</span></div></div><div class='wrap' style='padding-top:40px'><h2>Browse by Category</h2><div class='cat-grid' id='hCatGrid'></div></div><footer class='footer'><div class='fg'><div><h4>MediCart Pharmacy</h4><p>DBMS Project &mdash; Python + SQLite</p></div><div><h4>Categories</h4><a data-page='medicines'>Pain Relief</a><a data-page='medicines'>Vitamins</a><a data-page='medicines'>Baby Care</a></div><div><h4>Quick Links</h4><a data-page='prescriptions'>Prescriptions</a><a data-page='orders'>Orders</a><a data-page='about'>About Project</a></div><div><h4>Contact</h4><p>support@medicart.example</p><p>+91 484 234 5678</p></div></div><div class='fbot'><span>&copy; 2026 MediCart Pharmacy DBMS Project</span><span>Python 3 &bull; SQLite 3 &bull; 10-Table Schema</span></div></footer></section><section class='page' id='page-medicines'><div class='bc'><a data-page='home'>Home</a> &gt; <b>Medicines</b></div><div class='ml'><aside class='card'><h4>Filter Medicines</h4><div class='field' style='margin-top:12px'><label>Category</label><div id='fCats'></div></div><div class='field'><label>Max Price: &#8377;<span id='pv'>350</span></label><input type='range' id='pr' min='30' max='350' value='350' style='width:100%'></div><div class='field'><label><input type='checkbox' id='sf'> In Stock Only</label></div><div class='field'><label><input type='checkbox' id='nrf'> No Rx Required</label></div><button class='btn btn-ghost btn-block btn-sm' id='cf'>Reset Filters</button></aside><div><div class='mtb'><span class='muted small' id='rc'>Loading...</span><select id='ss' style='padding:7px 11px;border:1px solid var(--bd);border-radius:8px;background:var(--cbg)'><option value='top'>Popularity</option><option value='low'>Price Low&rarr;High</option><option value='high'>Price High&rarr;Low</option><option value='name'>Name A&ndash;Z</option></select></div><div class='mg' id='mGrid'></div></div></div></section><section class='page' id='page-detail'><div class='bc'><a data-page='home'>Home</a> &gt; <a data-page='medicines'>Medicines</a> &gt; <b id='crumb'>Detail</b></div><div class='dl'><div class='dimg' id='dImg'>&#128138;</div><div><span class='badge bg' id='dCat'>Category</span><h2 id='dName' style='margin:8px 0 4px'>Name</h2><p class='muted small' id='dMfr'></p><div id='dPrice' style='font-size:26px;color:var(--p7);margin:12px 0;font-family:Space Grotesk;font-weight:700'></div><span id='dStock' class='badge'></span><p style='margin-top:14px;line-height:1.8' id='dDesc' class='muted'></p></div><div class='card'><div class='field'><label>Quantity</label><input type='number' id='dQty' value='1' min='1' max='99' style='width:80px'></div><button class='btn btn-primary btn-block' id='addCartBtn' style='margin-bottom:10px'>Add to Cart</button><button class='btn btn-outline btn-block' id='buyNowBtn'>Buy Now</button><div class='divider'></div><p class='small muted' id='dRx'></p></div></div></section><section class='page' id='page-prescriptions'><div class='ph'><h2>Prescription Management</h2><p class='muted small' style='margin-top:4px'>Upload prescriptions for pharmacist verification. Stored in <code>prescriptions</code> table.</p></div><div class='two'><div class='card'><h4>Upload Prescription</h4><input type='file' id='rxFile' accept='image/*,.pdf' style='display:none'><div class='dropzone' id='rxZone' style='margin:14px 0'><p><b>Click to select file</b></p><p id='rxFN' class='small' style='color:var(--p7);font-weight:600;margin-top:5px'></p></div><div class='field'><label>Patient Name</label><input id='rxPat'></div><div class='field'><label>Prescribing Doctor</label><input id='rxDoc'></div><button class='btn btn-primary btn-block' id='rxBtn'>Submit for Verification</button></div><div class='card' style='padding:0;overflow:hidden'><h4 style='padding:16px 16px 0'>Submitted Prescriptions</h4><table style='margin-top:8px'><thead><tr><th>Date</th><th>Patient</th><th>Doctor</th><th>Status</th></tr></thead><tbody id='rxBody'></tbody></table></div></div></section><section class='page' id='page-cart'><div class='ph'><h2>Shopping Cart</h2></div><div class='two'><div class='card' style='padding:0;overflow:hidden'><table><thead><tr><th>Medicine</th><th>Price</th><th>Qty</th><th>Subtotal</th><th></th></tr></thead><tbody id='cartBody'></tbody></table></div><div class='card'><h4>Order Summary</h4><div class='sl'><span>Subtotal</span><span id='sumSub'>&#8377;0</span></div><div class='sl'><span>Delivery</span><span>&#8377;40</span></div><div class='sl tot'><span>Total</span><span id='sumTot'>&#8377;0</span></div><button class='btn btn-primary btn-block' style='margin-top:18px' id='chkBtn'>Proceed to Checkout &rarr;</button></div></div></section><section class='page' id='page-checkout'><div class='ph'><h2>Order Checkout</h2></div><div class='two'><div class='card'><h4>Delivery Details</h4><div class='field'><label>Recipient Name</label><input id='ckName'></div><div class='field'><label>Address</label><textarea id='ckAddr' rows='2'></textarea></div><div class='field'><label>Phone</label><input id='ckPhone'></div></div><div class='card'><h4>Order Recap</h4><div id='ckItems'></div><div class='sl tot'><span>Total Payable</span><span id='ckTot'>&#8377;0</span></div><button class='btn btn-primary btn-block' style='margin-top:18px' id='placeBtn'>Confirm &amp; Place Order</button></div></div></section><section class='page' id='page-orders'><div class='ph'><h2>Orders &amp; Tracking</h2></div><div class='two'><div class='card' style='padding:0;overflow:hidden'><table><thead><tr><th>Order ID</th><th>Date</th><th>Total</th><th>Status</th></tr></thead><tbody id='ordBody'></tbody></table></div><div class='card' id='ordDetail'><h4 id='odId'>Select an order</h4><div class='tracker' id='odTrack'></div><div id='odItems'></div><div id='statusUpdater' style='display:none;margin-top:14px'><div class='field'><label>Update Status (Admin)</label><select id='statusSel' style='padding:8px 11px;border:1px solid var(--bd);border-radius:8px;background:var(--cbg)'><option>Placed</option><option>Confirmed</option><option>Shipped</option><option>Delivered</option><option>Cancelled</option></select></div><button class='btn btn-outline btn-sm' id='statusBtn'>Update Status</button></div></div></div></section><section class='page' id='page-profile'><div class='ph'><h2>User Profile</h2></div><div class='two'><div class='card'><h3 id='pName'>Guest</h3><p class='muted small' id='pEmail' style='margin-top:4px'></p><span class='badge bg' id='pRole' style='margin-top:8px'>Customer</span><div class='divider'></div><p class='small muted'>&#128101; Total Orders: <b id='pOrdCount'>0</b></p><p class='small muted' style='margin-top:6px'>&#128274; Password stored as SHA-256 hash in DB</p><div style='margin-top:16px'><button class='btn btn-danger btn-sm' id='logoutBtn'>Sign Out</button></div></div><div class='card' style='padding:0;overflow:hidden'><h4 style='padding:14px 16px 0'>Recent Orders</h4><table style='margin-top:8px'><thead><tr><th>Order ID</th><th>Date</th><th>Total</th><th>Status</th></tr></thead><tbody id='pOrdBody'></tbody></table></div></div></section><section class='page' id='page-admin'><div class='ph'><div style='display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px'><div><h2>Admin Dashboard</h2><p class='muted small' style='margin-top:4px'>Pharmacy Management System &mdash; SQLite Database</p></div><span class='sbadge'>&#128203; pharmacy_dbms.db</span></div></div><div class='krow'><div class='kpi'><div class='lbl'>Total Revenue</div><div class='val' style='color:var(--p7)' id='kSales'>&#8377;0</div><div class='sub'>SUM(total) FROM orders</div></div><div class='kpi'><div class='lbl'>Total Orders</div><div class='val' id='kOrders'>0</div><div class='sub'>COUNT(*) FROM orders</div></div><div class='kpi'><div class='lbl'>Customers</div><div class='val' id='kCust'>0</div><div class='sub'>COUNT(*) FROM users</div></div><div class='kpi'><div class='lbl'>Stock Alerts</div><div class='val' style='color:var(--r6)' id='kStock'>0</div><div class='sub'>stock_batches table</div></div></div><div class='wrap' id='masterPanel' style='padding-top:18px;display:none'><div class='mpanel'><div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:12px'><h3 style='color:var(--pu)'>&#128081; Master Admin Controls</h3><span class='badge bp'>Master Access Only</span></div><p class='small muted' style='margin-bottom:14px'>Create new Admin accounts. Saved to <code style='background:var(--cbg);padding:1px 5px;border-radius:4px'>admins</code> table with SHA-256 hashed password and <code style='background:var(--cbg);padding:1px 5px;border-radius:4px'>is_master=0</code>.</p><div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px'><div class='field'><label>Full Name</label><input id='naName' placeholder='Dr. Rajesh Kumar'></div><div class='field'><label>Email</label><input id='naEmail' placeholder='rajesh@medicart.com'></div><div class='field'><label>Phone</label><input id='naPhone' placeholder='+91 98123 45678'></div><div class='field'><label>Password</label><input type='password' id='naPass'></div><div class='field'><label>Role / Position</label><input id='naRole' placeholder='Senior Pharmacist'></div><div class='field' style='justify-content:flex-end'><button class='btn btn-purple btn-block' id='createAdminBtn'>+ Create Admin</button></div></div></div></div><div class='wrap' style='padding-top:18px'><h3>Database Table Viewer</h3><div style='display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:14px'><div class='card' style='padding:0;overflow:hidden'><h4 style='padding:12px 14px 0;font-size:14px'>users <span class='badge bg' style='margin-left:4px;font-size:9px'>3NF</span></h4><table style='margin-top:6px'><thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Joined</th></tr></thead><tbody id='dUsers'></tbody></table></div><div class='card' style='padding:0;overflow:hidden'><h4 style='padding:12px 14px 0;font-size:14px'>admins <span class='badge bp' style='margin-left:4px;font-size:9px'>is_master</span></h4><table style='margin-top:6px'><thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead><tbody id='dAdmins'></tbody></table></div></div></div><div class='wrap' style='padding-top:18px;padding-bottom:48px'><h3>&#128200; Inventory &mdash; stock_batches JOIN medicines</h3><div class='card' style='padding:0;overflow:hidden;margin-top:12px'><table><thead><tr><th>Medicine</th><th>Batch No.</th><th>Quantity</th><th>Expiry</th><th>Status</th><th>Supplier</th></tr></thead><tbody id='dStock'></tbody></table></div></div></section><section class='page' id='page-reports'><div class='ph'><h2>&#128202; Sales &amp; Stock Reports</h2><p class='muted small' style='margin-top:4px'>Powered by SQL GROUP BY, JOIN, SUM, COUNT queries.</p></div><div class='krow'><div class='kpi'><div class='lbl'>Total Revenue</div><div class='val' style='color:var(--p7)' id='rRev'>&#8377;0</div><div class='sub'>SUM(total) FROM orders</div></div><div class='kpi'><div class='lbl'>Total Orders</div><div class='val' id='rOrds'>0</div><div class='sub'>COUNT(*) FROM orders</div></div><div class='kpi'><div class='lbl'>Customers</div><div class='val' id='rCust'>0</div><div class='sub'>COUNT(*) FROM users</div></div><div class='kpi'><div class='lbl'>Products</div><div class='val' id='rMeds'>0</div><div class='sub'>COUNT(*) FROM medicines</div></div></div><div class='wrap' style='padding-top:20px'><div style='display:grid;grid-template-columns:1.4fr 1fr;gap:20px'><div class='card'><h4>Revenue by Category <span class='mono' style='color:var(--t3);margin-left:6px'>GROUP BY cat.id</span></h4><div class='chart-wrap' id='catChart'></div><div style='display:flex;gap:8px;flex-wrap:wrap;margin-top:8px' id='catLegend'></div></div><div class='card'><h4>Orders by Status</h4><div id='statusChart' style='margin-top:12px'></div></div></div></div><div class='wrap' style='padding-top:18px'><div style='display:grid;grid-template-columns:1fr 1fr;gap:18px'><div class='card' style='padding:0;overflow:hidden'><h4 style='padding:14px 16px 0'>&#127942; Top 5 Medicines by Sales</h4><table style='margin-top:8px'><thead><tr><th>#</th><th>Medicine</th><th>Units Sold</th><th>Revenue</th></tr></thead><tbody id='topMeds'></tbody></table></div><div class='card' style='padding:0;overflow:hidden'><h4 style='padding:14px 16px 0'>&#9888; Stock Alerts <span class='badge br' id='alertCnt' style='margin-left:4px'>0</span></h4><table style='margin-top:8px'><thead><tr><th>Medicine</th><th>Batch</th><th>Qty</th><th>Expiry</th><th>Status</th></tr></thead><tbody id='stockAlerts'></tbody></table></div></div></div><div class='wrap' style='padding-top:18px;padding-bottom:48px'><div class='card' style='background:var(--sfbg)'><h4 style='margin-bottom:12px'>&#128203; SQL Queries Behind This Report</h4><pre style='font-size:12px;color:var(--t2);line-height:1.7;overflow-x:auto;white-space:pre-wrap'>-- Revenue by Category\nSELECT cat.name, SUM(oi.quantity * oi.unit_price) AS revenue\nFROM categories cat\nLEFT JOIN medicines m ON m.category_id = cat.id\nLEFT JOIN order_items oi ON oi.medicine_id = m.id\nGROUP BY cat.id ORDER BY revenue DESC;\n\n-- Top 5 Medicines by Units Sold\nSELECT m.name, SUM(oi.quantity) AS units_sold,\n       SUM(oi.quantity * oi.unit_price) AS revenue\nFROM medicines m LEFT JOIN order_items oi ON oi.medicine_id = m.id\nGROUP BY m.id ORDER BY units_sold DESC LIMIT 5;\n\n-- Stock Alerts\nSELECT m.name, sb.batch_no, sb.quantity, sb.expiry_date, sb.status\nFROM stock_batches sb JOIN medicines m ON sb.medicine_id = m.id\nWHERE sb.status != 'ok' ORDER BY sb.quantity ASC;</pre></div></div></section><section class='page' id='page-audit'><div class='ph'><div style='display:flex;align-items:center;gap:12px;flex-wrap:wrap'><h2>&#128221; System Audit Log</h2><span class='badge bp'>Master Admin Only</span></div><p class='muted small' style='margin-top:4px'>All key operations logged to <code style='background:var(--sfbg);padding:1px 5px;border-radius:4px'>audit_log</code> table.</p></div><div class='wrap' style='padding-top:12px;padding-bottom:48px'><div class='card' style='padding:0;overflow:hidden'><table><thead><tr><th>Timestamp</th><th>Action</th><th>Entity</th><th>Entity ID</th><th>User</th><th>Type</th><th>Details</th></tr></thead><tbody id='auditBody'></tbody></table></div></div></section><section class='page' id='page-medmgmt'><div class='ph'><h2>&#128138; Medicine Management</h2><p class='muted small' style='margin-top:4px'>Add and remove from the <code style='background:var(--sfbg);padding:1px 5px;border-radius:4px'>medicines</code> table.</p></div><div class='two'><div class='card'><h4>Add New Medicine</h4><div class='field'><label>Medicine Name</label><input id='mmName' placeholder='e.g. Aspirin 75mg'></div><div class='field'><label>Category</label><select id='mmCat'></select></div><div class='field'><label>Price (&#8377;)</label><input type='number' id='mmPrice' placeholder='0.00' min='0'></div><div class='field'><label>Stock Quantity</label><input type='number' id='mmStock' placeholder='0' min='0'></div><div class='field'><label>Manufacturer</label><input id='mmMfr' placeholder='e.g. Sun Pharma'></div><div class='field'><label>Description</label><textarea id='mmDesc' rows='2'></textarea></div><div class='field'><label><input type='checkbox' id='mmRx'> Prescription Required (Rx)</label></div><button class='btn btn-primary btn-block' id='mmAddBtn'>+ Add to Database</button></div><div class='card' style='padding:0;overflow:hidden'><div style='display:flex;align-items:center;justify-content:space-between;padding:14px 16px 0'><h4>All Medicines <span class='badge bg' id='medTotalBadge'>0</span></h4><input id='mmSearch' placeholder='Filter...' style='padding:5px 10px;border:1px solid var(--bd);border-radius:6px;font-size:13px;width:130px;background:var(--cbg)'></div><table style='margin-top:8px'><thead><tr><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Rx</th><th>Action</th></tr></thead><tbody id='mmBody'></tbody></table></div></div></section><section class='page' id='page-suppliers'><div class='ph'><h2>Supplier Management</h2></div><div class='two'><div class='card'><h4>Add Supplier</h4><div class='field'><label>Company Name</label><input id='supName'></div><div class='field'><label>Contact Person</label><input id='supContact'></div><div class='field'><label>Phone</label><input id='supPhone'></div><div class='field'><label>Email</label><input id='supEmail'></div><div class='field'><label>Product Categories</label><input id='supCats'></div><div class='field'><label>Address</label><input id='supAddr'></div><button class='btn btn-primary btn-block' id='supBtn'>Save Supplier</button></div><div class='card' style='padding:0;overflow:hidden'><table style='margin-top:10px'><thead><tr><th>Company</th><th>Contact</th><th>Email</th><th>Categories</th><th></th></tr></thead><tbody id='supBody'></tbody></table></div></div></section><section class='page' id='page-login'><div class='aw'><div class='ab'><div style='text-align:center;margin-bottom:16px'><span class='sbadge'>&#128274; SHA-256 Password Hashing</span></div><div class='atabs'><button class='atab active' data-auth='login'>Sign In</button><button class='atab' data-auth='signup'>Create Account</button></div><div id='aLogin'><div class='field'><label>Account Type</label><select id='lType'><option value='auto'>Auto Detect</option><option value='user'>Customer (users table)</option><option value='admin'>Admin (admins table)</option></select></div><div class='field'><label>Email</label><input id='lEmail' value='master@medicart.com'></div><div class='field'><label>Password</label><input type='password' id='lPass' value='master123'></div><button class='btn btn-primary btn-block' id='loginBtn'>Sign In</button><div class='divider'></div><p class='small muted' style='text-align:center;margin-bottom:10px'>Quick Login:</p><div style='display:flex;flex-direction:column;gap:7px'><button class='btn btn-ghost btn-sm btn-block' id='dm' style='border-color:var(--pu);color:var(--pu)'>&#128081; Master Admin &mdash; master@medicart.com</button><button class='btn btn-ghost btn-sm btn-block' id='da'>&#128994; Pharmacist &mdash; admin@medicart.com</button><button class='btn btn-ghost btn-sm btn-block' id='dc'>&#128309; Customer &mdash; john@example.com</button></div></div><div id='aSignup' style='display:none'><div class='field'><label>Full Name *</label><input id='sName' placeholder='John Doe'></div><div class='field'><label>Email Address *</label><input id='sEmail' placeholder='john@example.com'></div><div class='field'><label>Phone Number</label><input id='sPhone' placeholder='+91 98765 43210'></div><div class='field'><label>Password *</label><input type='password' id='sPass' placeholder='Create password'></div><div class='field'><label>Confirm Password *</label><input type='password' id='sPassConfirm' placeholder='Confirm password'></div><div style='background:var(--sfbg);padding:10px 12px;border-radius:8px;border:1px solid var(--bd);margin-bottom:14px;font-size:12px;color:var(--t3);line-height:1.6'>&#128100; <b>Customer Account</b>: Stored in <code style='color:var(--p7)'>users</code> table with SHA-256 hash.<br>&#128081; <i>Need an Admin account?</i> Admin logins can only be created by Master Admin (<code>master@medicart.com</code>) from the Admin Portal.</div><button class='btn btn-primary btn-block' id='signupBtn'>Create Customer Account</button></div></div></div></section><section class='page' id='page-about'><div class='ph'><h2>About This DBMS Project</h2></div><div class='wrap' style='padding-top:12px;padding-bottom:40px'><div style='display:grid;grid-template-columns:1fr 1fr;gap:18px'><div class='card'><h4>&#128203; Database Schema</h4><p class='muted small' style='margin-top:8px;line-height:1.8'>10 normalized tables in 3NF:<br>categories &bull; users &bull; admins &bull; medicines<br>orders &bull; order_items &bull; prescriptions<br>suppliers &bull; stock_batches &bull; audit_log</p></div><div class='card'><h4>&#128274; Security</h4><p class='muted small' style='margin-top:8px;line-height:1.8'>&bull; SHA-256 hashing with PW_SALT<br>&bull; Role-based access (Master/Admin/Customer)<br>&bull; Foreign key constraints enforced<br>&bull; Full audit trail of all operations</p></div><div class='card'><h4>&#9881; Stack</h4><p class='muted small' style='margin-top:8px;line-height:1.8'>&bull; Python 3 (http.server, sqlite3, hashlib)<br>&bull; SQLite 3 database<br>&bull; Zero external dependencies<br>&bull; REST API with JSON responses</p></div><div class='card'><h4>&#128202; SQL Features</h4><p class='muted small' style='margin-top:8px;line-height:1.8'>&bull; JOIN (medicines+categories+order_items)<br>&bull; GROUP BY + SUM for revenue reports<br>&bull; FOREIGN KEY with PRAGMA enforcement<br>&bull; AUTOINCREMENT PKs, UNIQUE constraints</p></div></div></div></section><section class='page' id='page-contact'><div class='ph'><h2>Contact Us</h2></div><div class='two'><div class='card'><div class='field'><label>Name</label><input id='cName'></div><div class='field'><label>Email</label><input id='cEmail'></div><div class='field'><label>Message</label><textarea id='cMsg' rows='4'></textarea></div><button class='btn btn-primary' id='cBtn'>Send Message</button></div><div class='card'><h4>MediCart Pharmacy</h4><p class='muted small' style='margin-top:8px;line-height:1.8'>44, MG Road, Kochi, Kerala<br>Phone: +91 484 234 5678<br>Email: support@medicart.example<br><br>Open daily 8 AM &ndash; 10 PM</p></div></div></section></main>"

JS = '\n<script>\nvar MEDS=[],CATS=[],STOCK=[],suppliers=[],orders=[],prescriptions=[],dbUsers=[],dbAdmins=[];\nvar currentUser=null,cart=[],currentMedId=1,selCat=null,currentOrdId=null;\nfunction $(s){return document.querySelector(s)}\nfunction $$(s){return document.querySelectorAll(s)}\nfunction inr(n){return \'&#8377;\'+Number(n).toLocaleString(\'en-IN\')}\nfunction medById(id){return MEDS.find(function(m){return m.id===id||m.id===Number(id)})}\nfunction today(){return new Date().toISOString().slice(0,10)}\nfunction toast(msg,ok){\n  if(ok===undefined)ok=true;\n  $(\'#tmsg\').textContent=msg;var t=$(\'#toast\');\n  t.style.background=ok?\'var(--p9)\':\'var(--r6)\';t.classList.add(\'show\');\n  clearTimeout(window._tt);window._tt=setTimeout(function(){t.classList.remove(\'show\')},3200);\n}\nfunction nav(page){\n  $$(\'.page\').forEach(function(p){p.classList.remove(\'active\')});\n  var t=$(\'#page-\'+page);if(t)t.classList.add(\'active\');\n  window.scrollTo({top:0,behavior:\'instant\'});\n  var adm=[\'admin\',\'medmgmt\',\'suppliers\',\'reports\',\'audit\'].indexOf(page)>=0;\n  $(\'#cNav\').style.display=adm?\'none\':\'block\';$(\'#aNav\').style.display=adm?\'block\':\'none\';\n  if(page===\'medicines\')renderMeds();if(page===\'cart\')renderCart();\n  if(page===\'checkout\')renderCheckout();if(page===\'orders\')renderOrders();\n  if(page===\'profile\')renderProfile();if(page===\'admin\')renderAdmin();\n  if(page===\'medmgmt\')renderMedMgmt();if(page===\'suppliers\')renderSuppliers();\n  if(page===\'prescriptions\')renderRx();if(page===\'reports\')renderReports();\n  if(page===\'audit\')renderAudit();\n}\ndocument.body.addEventListener(\'click\',function(e){\n  var l=e.target.closest(\'[data-page]\');if(l){e.preventDefault();nav(l.dataset.page);}\n  var cc=e.target.closest(\'[data-cat]\');if(cc){selCat=cc.dataset.cat;nav(\'medicines\');}\n  var om=e.target.closest(\'[data-om]\');if(om){openDetail(+om.dataset.om);return;}\n  var qa=e.target.closest(\'[data-qa]\');if(qa)addCart(+qa.dataset.qa,1);\n  var rm=e.target.closest(\'[data-rm]\');\n  if(rm){cart=cart.filter(function(c){return c.id!==+rm.dataset.rm});$(\'#cc\').textContent=cart.reduce(function(s,c){return s+c.qty},0);renderCart();}\n  var ds=e.target.closest(\'[data-ds]\');\n  if(ds){var sid=+ds.dataset.ds;fetch(\'/api/suppliers/\'+sid,{method:\'DELETE\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({by_email:currentUser?currentUser.email:\'admin\'})}).catch(function(){});suppliers=suppliers.filter(function(x){return x.id!==sid});renderSuppliers();toast(\'Supplier removed\');}\n  var dm=e.target.closest(\'[data-dm]\');\n  if(dm){var mid=+dm.dataset.dm;var mx=medById(mid);\n    if(!confirm(\'Delete "\'+(mx?mx.name:\'this medicine\')+\'"?\'))return;\n    fetch(\'/api/medicines/\'+mid,{method:\'DELETE\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({by_email:currentUser?currentUser.email:\'admin\'})}).then(function(r){return r.json()}).then(function(d){if(d.success){toast(\'Medicine deleted\');syncAll().then(renderMedMgmt);}else toast(d.error||\'Failed\',false)}).catch(function(){toast(\'Error\',false)});}\n  var row=e.target.closest(\'[data-oid]\');\n  if(row){var o=orders.find(function(x){return x.id===row.dataset.oid});if(!o)return;\n    currentOrdId=o.id;$(\'#odId\').textContent=\'Order: \'+o.id;\n    var steps=[\'Placed\',\'Confirmed\',\'Shipped\',\'Delivered\'],si=steps.indexOf(o.status);\n    $(\'#odTrack\').innerHTML=steps.map(function(s,i){return \'<div class="ts \'+(i<=si?\'done\':\'\')+\'"><div class="dot">\'+(i<=si?\'&#10003;\':i+1)+\'</div><div class="tline"></div><small>\'+s+\'</small></div>\'}).join(\'\');\n    $(\'#odItems\').innerHTML=(o.items||[]).map(function(it){return \'<div class="sl"><span>\'+(it.medicine_name||\'Item\')+\' x\'+(it.qty||it.quantity||1)+\'</span><span>\'+inr((it.unit_price||0)*(it.qty||it.quantity||1))+\'</span></div>\'}).join(\'\');\n    var isAdm=currentUser&&currentUser.type===\'admin\';\n    $(\'#statusUpdater\').style.display=isAdm?\'block\':\'none\';\n    if(isAdm)$(\'#statusSel\').value=o.status;}\n});\ndocument.body.addEventListener(\'change\',function(e){\n  var cq=e.target.closest(\'[data-cqty]\');\n  if(cq){var c=cart.find(function(x){return x.id===+cq.dataset.cqty});if(c){c.qty=Math.max(1,+cq.value);renderCart();}}\n});\n$(\'#tgl\').addEventListener(\'click\',function(){var d=document.documentElement;d.setAttribute(\'data-theme\',d.getAttribute(\'data-theme\')===\'dark\'?\'light\':\'dark\')});\nfunction renderHomeCats(){\n  $(\'#hCatGrid\').innerHTML=CATS.map(function(c){return \'<div class="cat-card" data-cat="\'+c.slug+\'"><div class="icon">\'+c.icon+\'</div><b>\'+c.name+\'</b><br><span class="small muted">\'+c.description.slice(0,28)+\'...</span></div>\'}).join(\'\');\n}\nfunction renderFilterCats(){\n  $(\'#fCats\').innerHTML=CATS.map(function(c){return \'<label style="display:block;margin-bottom:4px"><input type="checkbox" class="cc" value="\'+c.slug+\'" \'+(selCat===c.slug?\'checked\':\'\')+\'>\'+c.icon+\' \'+c.name+\'</label>\'}).join(\'\');\n}\nfunction filteredMeds(){\n  var q=($(\'#si\').value||\'\').toLowerCase();\n  var ch=[].slice.call($$(\'.cc:checked\')).map(function(x){return x.value});\n  var mp=+$(\'#pr\').value,so=$(\'#sf\').checked,nr=$(\'#nrf\').checked;\n  var list=MEDS.filter(function(m){\n    if(q&&m.name.toLowerCase().indexOf(q)<0)return false;\n    if(ch.length&&ch.indexOf(m.cat)<0)return false;\n    if(m.price>mp)return false;\n    if(so&&m.stock===0)return false;\n    if(nr&&m.rx_required)return false;\n    return true;\n  });\n  var s=$(\'#ss\').value;\n  if(s===\'low\')list.sort(function(a,b){return a.price-b.price});\n  else if(s===\'high\')list.sort(function(a,b){return b.price-a.price});\n  else if(s===\'name\')list.sort(function(a,b){return a.name.localeCompare(b.name)});\n  else list.sort(function(a,b){return b.reviews-a.reviews});\n  return list;\n}\nfunction medCard(m){\n  var inStock=m.stock>0;\n  return \'<div class="mc"><div style="font-size:22px">\'+(m.cat_icon||\'&#128138;\')+\'</div>\'+\n    \'<h4 data-om="\'+m.id+\'" style="cursor:pointer;color:var(--p7);line-height:1.3">\'+m.name+\'</h4>\'+\n    \'<p class="muted small">\'+m.manufacturer+\'</p>\'+\n    \'<div style="display:flex;align-items:center;justify-content:space-between"><div style="font-family:Space Grotesk;font-weight:700;font-size:17px">\'+inr(m.price)+\'</div>\'+(m.rx_required?\'<span class="badge br">Rx</span>\':\'\')+\'</div>\'+\n    \'<div style="display:flex;align-items:center;justify-content:space-between;gap:8px">\'+\n    (inStock?\'<span class="badge bg">Stock: \'+m.stock+\'</span>\':\'<span class="badge br">Out of Stock</span>\')+\n    \'<button class="btn btn-primary btn-sm" data-qa="\'+m.id+\'" \'+(inStock?\'\':\'disabled\')+\'>Add to Cart</button></div></div>\';\n}\nfunction renderMeds(){renderFilterCats();var list=filteredMeds();$(\'#mGrid\').innerHTML=list.map(medCard).join(\'\')||\'<p class="muted" style="padding:20px">No medicines match filters.</p>\';$(\'#rc\').textContent=list.length+\' medicine\'+(list.length!==1?\'s\':\'\');}\n$(\'#pr\').addEventListener(\'input\',function(){$(\'#pv\').textContent=$(\'#pr\').value;renderMeds()});\n$(\'#ss\').addEventListener(\'change\',renderMeds);$(\'#sf\').addEventListener(\'change\',renderMeds);$(\'#nrf\').addEventListener(\'change\',renderMeds);\n$(\'#cf\').addEventListener(\'click\',function(){selCat=null;$(\'#pr\').value=350;$(\'#pv\').textContent=350;$(\'#sf\').checked=false;$(\'#nrf\').checked=false;renderMeds()});\n$(\'#si\').addEventListener(\'input\',function(){if($(\'#page-medicines\').classList.contains(\'active\'))renderMeds()});\nfunction openDetail(id){\n  currentMedId=id;var m=medById(id);if(!m)return;\n  $(\'#crumb\').textContent=m.name;$(\'#dName\').textContent=m.name;$(\'#dImg\').textContent=m.cat_icon||\'&#128138;\';\n  $(\'#dCat\').textContent=m.cat_name||m.cat;$(\'#dPrice\').textContent=inr(m.price);$(\'#dMfr\').textContent=m.manufacturer;$(\'#dDesc\').textContent=m.description||\'\';\n  $(\'#dRx\').textContent=m.rx_required?\'Prescription (Rx) required.\':\'No prescription required.\';\n  var stk=m.stock>0;$(\'#dStock\').className=\'badge \'+(stk?\'bg\':\'br\');$(\'#dStock\').textContent=stk?(\'In Stock (\'+m.stock+\' units)\'):\'Out of Stock\';$(\'#addCartBtn\').disabled=!stk;nav(\'detail\');\n}\n$(\'#addCartBtn\').addEventListener(\'click\',function(){addCart(currentMedId,+$(\'#dQty\').value||1)});\n$(\'#buyNowBtn\').addEventListener(\'click\',function(){addCart(currentMedId,+$(\'#dQty\').value||1);nav(\'cart\')});\nfunction addCart(id,qty){\n  var ex=cart.find(function(c){return c.id===id});\n  if(ex)ex.qty+=qty;else cart.push({id:id,qty:qty,price:medById(id)?medById(id).price:0});\n  $(\'#cc\').textContent=cart.reduce(function(s,c){return s+c.qty},0);toast(\'Added to cart\');\n}\nfunction renderCart(){\n  $(\'#cartBody\').innerHTML=cart.map(function(c){var m=medById(c.id);return \'<tr><td><b>\'+(m?m.name:\'Item\')+\'</b></td><td>\'+inr(m?m.price:0)+\'</td><td><input type="number" value="\'+c.qty+\'" min="1" max="99" style="width:55px;padding:4px 6px;border:1px solid var(--bd);border-radius:6px" data-cqty="\'+c.id+\'"></td><td>\'+inr((m?m.price:0)*c.qty)+\'</td><td><button class="btn btn-danger btn-sm" data-rm="\'+c.id+\'">&#128465;</button></td></tr>\'}).join(\'\')||\'<tr><td colspan="5" style="text-align:center;padding:24px;color:var(--t3)">Cart is empty</td></tr>\';\n  var tot=cart.reduce(function(s,c){return s+(medById(c.id)?medById(c.id).price:0)*c.qty},0);\n  $(\'#sumSub\').textContent=inr(tot);$(\'#sumTot\').textContent=inr(tot>0?tot+40:0);\n}\n$(\'#chkBtn\').addEventListener(\'click\',function(){if(!cart.length){toast(\'Cart is empty\',false);return;}nav(\'checkout\')});\nfunction renderCheckout(){\n  var sub=cart.reduce(function(s,c){return s+(medById(c.id)?medById(c.id).price:0)*c.qty},0);\n  $(\'#ckItems\').innerHTML=cart.map(function(c){var m=medById(c.id);return \'<div class="sl"><span>\'+(m?m.name:\'Item\')+\' x\'+c.qty+\'</span><span>\'+inr((m?m.price:0)*c.qty)+\'</span></div>\'}).join(\'\');\n  $(\'#ckTot\').textContent=inr(sub+40);\n  if(currentUser){$(\'#ckName\').value=currentUser.name||\'\';$(\'#ckPhone\').value=currentUser.phone||\'\';}\n}\n$(\'#placeBtn\').addEventListener(\'click\',function(){\n  if(!cart.length){toast(\'Cart is empty\',false);return;}\n  var oid=\'ORD-\'+Math.floor(Math.random()*9000+1000);\n  var sub=cart.reduce(function(s,c){return s+(medById(c.id)?medById(c.id).price:0)*c.qty},0);\n  var payload={id:oid,user_email:currentUser?currentUser.email:\'guest@medicart.com\',date:today(),total:sub+40,delivery_name:$(\'#ckName\').value,delivery_address:$(\'#ckAddr\').value,delivery_phone:$(\'#ckPhone\').value,items:cart.map(function(c){return{id:c.id,qty:c.qty,price:medById(c.id)?medById(c.id).price:0}})};\n  fetch(\'/api/orders\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(payload)}).then(function(r){return r.json()}).then(function(d){\n    if(d.success){orders.unshift({id:oid,user_email:payload.user_email,date:payload.date,total:payload.total,status:\'Placed\',items:cart.map(function(c){var m=medById(c.id);return{medicine_id:c.id,quantity:c.qty,unit_price:m?m.price:0,medicine_name:m?m.name:\'Item\'}})});cart=[];$(\'#cc\').textContent=0;toast(\'Order \'+oid+\' placed!\');nav(\'orders\');}\n    else toast(d.message||\'Order failed\',false);\n  }).catch(function(){toast(\'Connection error\',false)});\n});\nfunction renderOrders(){\n  $(\'#ordBody\').innerHTML=orders.map(function(o){var cls=o.status===\'Delivered\'?\'bg\':o.status===\'Cancelled\'?\'br\':\'ba\';return \'<tr data-oid="\'+o.id+\'" style="cursor:pointer"><td><b>\'+o.id+\'</b></td><td>\'+o.date+\'</td><td>\'+inr(o.total)+\'</td><td><span class="badge \'+cls+\'">\'+o.status+\'</span></td></tr>\'}).join(\'\')||\'<tr><td colspan="4" style="text-align:center;padding:20px;color:var(--t3)">No orders yet</td></tr>\';\n}\n$(\'#statusBtn\').addEventListener(\'click\',function(){\n  if(!currentOrdId||!currentUser)return;\n  var ns=$(\'#statusSel\').value;\n  fetch(\'/api/orders/\'+currentOrdId+\'/status\',{method:\'PATCH\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({status:ns,by_email:currentUser.email})}).then(function(r){return r.json()}).then(function(d){if(d.success){var o=orders.find(function(x){return x.id===currentOrdId});if(o)o.status=ns;toast(\'Status: \'+ns);renderOrders();}else toast(d.message||\'Failed\',false)}).catch(function(){toast(\'Error\',false)});\n});\nfunction renderRx(){\n  $(\'#rxBody\').innerHTML=prescriptions.map(function(p){return \'<tr><td>\'+p.date+\'</td><td>\'+(p.patient_name||\'\')+\'</td><td>\'+(p.doctor_name||\'\')+\'</td><td><span class="badge \'+(p.status===\'Verified\'?\'bg\':\'ba\')+\'">\'+p.status+\'</span></td></tr>\'}).join(\'\')||\'<tr><td colspan="4" style="text-align:center;padding:18px;color:var(--t3)">No prescriptions submitted</td></tr>\';\n}\n$(\'#rxZone\').addEventListener(\'click\',function(){$(\'#rxFile\').click()});\n$(\'#rxFile\').addEventListener(\'change\',function(e){if(e.target.files[0])$(\'#rxFN\').textContent=\'Selected: \'+e.target.files[0].name});\n$(\'#rxBtn\').addEventListener(\'click\',function(){\n  var patient=$(\'#rxPat\').value.trim(),doctor=$(\'#rxDoc\').value.trim();\n  if(!patient||!doctor){toast(\'Enter patient and doctor name\',false);return;}\n  var rec={file:$(\'#rxFN\').textContent||\'prescription.pdf\',patient:patient,doctor:doctor,date:today(),user_email:currentUser?currentUser.email:\'\'};\n  fetch(\'/api/prescriptions\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(rec)}).catch(function(){});\n  prescriptions.unshift({filename:rec.file,patient_name:patient,doctor_name:doctor,date:rec.date,status:\'Pending\',id:Date.now()});\n  toast(\'Prescription submitted!\');renderRx();$(\'#rxPat\').value=\'\';$(\'#rxDoc\').value=\'\';$(\'#rxFN\').textContent=\'\';\n});\nfunction renderProfile(){\n  if(!currentUser){$(\'#pName\').textContent=\'Not logged in\';return;}\n  $(\'#pName\').textContent=currentUser.name;$(\'#pEmail\').textContent=currentUser.email;\n  $(\'#pRole\').innerHTML=currentUser.type===\'admin\'?(currentUser.is_master?\'&#128081; Master Admin\':\'Pharmacist Admin\'):\'Customer\';\n  var myOrds=orders.filter(function(o){return o.user_email===currentUser.email||currentUser.type===\'admin\'});\n  $(\'#pOrdCount\').textContent=myOrds.length;\n  $(\'#pOrdBody\').innerHTML=myOrds.slice(0,6).map(function(o){return \'<tr><td>\'+o.id+\'</td><td>\'+o.date+\'</td><td>\'+inr(o.total)+\'</td><td><span class="badge \'+(o.status===\'Delivered\'?\'bg\':\'ba\')+\'">\'+o.status+\'</span></td></tr>\'}).join(\'\');\n}\n$(\'#logoutBtn\').addEventListener(\'click\',function(){currentUser=null;$(\'#accBtn\').textContent=\'Login\';toast(\'Signed out\');nav(\'home\')});\nfunction renderAdmin(){\n  if(!currentUser)return;\n  $(\'#aBadge\').innerHTML=currentUser.is_master?\'&#128081; Master Admin\':(\'Admin: \'+currentUser.name.split(\' \')[0]);\n  $(\'#masterPanel\').style.display=currentUser.is_master?\'block\':\'none\';\n  $(\'#auditLink\').style.display=currentUser.is_master?\'block\':\'none\';\n  var rev=orders.reduce(function(s,o){return s+o.total},0);\n  $(\'#kSales\').textContent=inr(rev);$(\'#kOrders\').textContent=orders.length;$(\'#kCust\').textContent=dbUsers.length;\n  $(\'#kStock\').textContent=STOCK.filter(function(s){return s.status!==\'ok\'}).length;\n  $(\'#dUsers\').innerHTML=dbUsers.map(function(u){return \'<tr><td>\'+u.name+\'</td><td class="small">\'+u.email+\'</td><td>\'+(u.phone||\'-\')+\'</td><td class="small muted">\'+(u.created_at||\'\').slice(0,10)+\'</td></tr>\'}).join(\'\')||\'<tr><td colspan="4" style="text-align:center;color:var(--t3)">No users</td></tr>\';\n  $(\'#dAdmins\').innerHTML=dbAdmins.map(function(a){return \'<tr><td>\'+a.name+(a.is_master?\' <span class="badge bp" style="font-size:9px">Master</span>\':\'\')+\'</td><td class="small">\'+a.email+\'</td><td><span class="badge bg">\'+a.role+\'</span></td></tr>\'}).join(\'\');\n  $(\'#dStock\').innerHTML=STOCK.map(function(s){var b=s.status===\'ok\'?\'bg\':s.status===\'low\'?\'ba\':\'br\';return \'<tr><td>\'+(s.medicine_name||\'\')+\'</td><td class="mono">\'+(s.batch_no||\'\')+\'</td><td>\'+(s.quantity||0)+\'</td><td>\'+(s.expiry_date||\'\')+\'</td><td><span class="badge \'+b+\'">\'+s.status+\'</span></td><td class="muted small">\'+(s.supplier_id?\'Supplier #\'+s.supplier_id:\'-\')+\'</td></tr>\'}).join(\'\');\n}\n$(\'#createAdminBtn\').addEventListener(\'click\',function(){\n  var name=$(\'#naName\').value.trim(),email=$(\'#naEmail\').value.trim(),phone=$(\'#naPhone\').value.trim(),pass=$(\'#naPass\').value.trim(),role=$(\'#naRole\').value.trim()||\'Pharmacist\';\n  if(!name||!email||!pass){toast(\'Name, email and password required\',false);return;}\n  fetch(\'/api/auth/create-admin\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({name:name,email:email,phone:phone,password:pass,role:role,by_email:currentUser?currentUser.email:\'master\'})}).then(function(r){return r.json()}).then(function(d){if(d.success){toast(\'Admin account for \'+name+\' created!\');[\'naName\',\'naEmail\',\'naPhone\',\'naPass\',\'naRole\'].forEach(function(id){$(\'#\'+id).value=\'\'});syncAll().then(renderAdmin);}else toast(d.message||\'Failed\',false)}).catch(function(){toast(\'Error\',false)});\n});\nfunction renderReports(){\n  Promise.all([fetch(\'/api/reports/sales\').then(function(r){return r.json()}),fetch(\'/api/reports/stock\').then(function(r){return r.json()})]).then(function(res){\n    var sales=res[0],stock=res[1];\n    $(\'#rRev\').textContent=inr(sales.total_revenue||0);$(\'#rOrds\').textContent=sales.total_orders||0;$(\'#rCust\').textContent=sales.total_customers||0;$(\'#rMeds\').textContent=sales.total_medicines||0;\n    var cats=sales.by_category||[];var maxRev=Math.max.apply(null,cats.map(function(c){return c.revenue}).concat([1]));\n    $(\'#catChart\').innerHTML=cats.map(function(c){return \'<div class="bar-col"><div class="bar-val">\'+(c.revenue>0?inr(c.revenue):\'\')+\'</div><div class="bar" style="height:\'+Math.max(4,(c.revenue/maxRev*140)).toFixed(0)+\'px"></div><div class="bar-lbl">\'+c.name+\'</div></div>\'}).join(\'\');\n    $(\'#catLegend\').innerHTML=cats.map(function(c){return \'<span class="badge bg">\'+(c.icon||\'\')+\'</span>\'}).join(\'\');\n    var byStatus=sales.by_status||[];\n    $(\'#statusChart\').innerHTML=byStatus.map(function(s){var cls=s.status===\'Delivered\'?\'bg\':s.status===\'Cancelled\'?\'br\':\'ba\';return \'<div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--bd)"><span>\'+s.status+\'</span><span class="badge \'+cls+\'">\'+s.cnt+\' orders</span></div>\'}).join(\'\')||\'<p class="muted small" style="padding:10px">No orders yet</p>\';\n    var top=sales.top_medicines||[];\n    $(\'#topMeds\').innerHTML=top.map(function(m,i){return \'<tr><td><b>\'+(i+1)+\'</b></td><td>\'+m.name+\'</td><td>\'+m.units_sold+\'</td><td>\'+inr(m.revenue)+\'</td></tr>\'}).join(\'\')||\'<tr><td colspan="4" style="text-align:center;color:var(--t3)">No sales data yet</td></tr>\';\n    var alerts=stock.alerts||[];\n    $(\'#alertCnt\').textContent=alerts.length;\n    $(\'#stockAlerts\').innerHTML=alerts.map(function(a){return \'<tr><td>\'+a.medicine_name+\'</td><td class="mono">\'+a.batch_no+\'</td><td>\'+a.quantity+\'</td><td>\'+a.expiry_date+\'</td><td><span class="badge \'+(a.status===\'out\'?\'br\':\'ba\')+\'">\'+a.status+\'</span></td></tr>\'}).join(\'\')||\'<tr><td colspan="5" style="text-align:center;color:var(--t3)">All stock levels normal</td></tr>\';\n  }).catch(function(){toast(\'Error loading reports\',false)});\n}\nfunction renderAudit(){\n  if(!currentUser||!currentUser.is_master){$(\'#auditBody\').innerHTML=\'<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--r6)">&#128274; Master Admin access required</td></tr>\';return;}\n  fetch(\'/api/audit\').then(function(r){return r.json()}).then(function(data){\n    $(\'#auditBody\').innerHTML=data.map(function(a){var cls=a.action.indexOf(\'DELETE\')>=0?\'br\':a.action.indexOf(\'LOGIN\')>=0?\'bg\':\'ba\';var ucls=a.user_type===\'master\'?\'bp\':a.user_type===\'admin\'?\'bg\':\'ba\';return \'<tr><td class="mono small">\'+a.timestamp.replace(\'T\',\' \').slice(0,19)+\'</td><td><span class="badge \'+cls+\'">\'+a.action+\'</span></td><td class="mono small">\'+a.entity+\'</td><td class="mono small">\'+a.entity_id+\'</td><td class="small">\'+a.user_email+\'</td><td><span class="badge \'+ucls+\'">\'+a.user_type+\'</span></td><td class="small muted">\'+a.details+\'</td></tr>\'}).join(\'\')||\'<tr><td colspan="7" style="text-align:center;color:var(--t3)">No audit records yet</td></tr>\';\n  }).catch(function(){toast(\'Error loading audit log\',false)});\n}\nfunction renderMedMgmt(){\n  $(\'#mmCat\').innerHTML=CATS.map(function(c){return \'<option value="\'+c.id+\'">\'+c.icon+\' \'+c.name+\'</option>\'}).join(\'\');\n  var q=($(\'#mmSearch\').value||\'\').toLowerCase();var filtered=MEDS.filter(function(m){return !q||m.name.toLowerCase().indexOf(q)>=0});\n  $(\'#medTotalBadge\').textContent=MEDS.length;\n  $(\'#mmBody\').innerHTML=filtered.map(function(m){return \'<tr><td><b>\'+m.name+\'</b></td><td>\'+(m.cat_icon||\'\')+(m.cat_name||m.cat)+\'</td><td>\'+inr(m.price)+\'</td><td>\'+m.stock+\'</td><td>\'+(m.rx_required?\'<span class="badge br">Rx</span>\':\'<span class="badge bg">OTC</span>\')+\'</td><td><button class="btn btn-danger btn-sm" data-dm="\'+m.id+\'">Delete</button></td></tr>\'}).join(\'\')||\'<tr><td colspan="6" style="text-align:center;color:var(--t3)">No medicines</td></tr>\';\n}\n$(\'#mmSearch\').addEventListener(\'input\',renderMedMgmt);\n$(\'#mmAddBtn\').addEventListener(\'click\',function(){\n  var name=$(\'#mmName\').value.trim(),mfr=$(\'#mmMfr\').value.trim();\n  if(!name||!mfr){toast(\'Name and manufacturer required\',false);return;}\n  var payload={name:name,category_id:+$(\'#mmCat\').value,price:+$(\'#mmPrice\').value||0,stock:+$(\'#mmStock\').value||0,rx:$(\'#mmRx\').checked?1:0,manufacturer:mfr,description:$(\'#mmDesc\').value,by_email:currentUser?currentUser.email:\'admin\'};\n  fetch(\'/api/medicines\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(payload)}).then(function(r){return r.json()}).then(function(d){if(d.success){toast(\'Medicine "\'+name+\'" added!\');[\'mmName\',\'mmPrice\',\'mmStock\',\'mmMfr\',\'mmDesc\'].forEach(function(id){$(\'#\'+id).value=\'\'});$(\'#mmRx\').checked=false;syncAll().then(renderMedMgmt);}else toast(d.message||\'Failed\',false)}).catch(function(){toast(\'Error\',false)});\n});\nfunction renderSuppliers(){\n  $(\'#supBody\').innerHTML=suppliers.map(function(s){return \'<tr><td><b>\'+s.name+\'</b></td><td>\'+(s.contact_person||s.contact||\'\')+\'</td><td class="small">\'+s.email+\'</td><td class="small muted">\'+(s.categories||s.cats||\'\')+\'</td><td><button class="btn btn-danger btn-sm" data-ds="\'+s.id+\'">&#128465;</button></td></tr>\'}).join(\'\');\n}\n$(\'#supBtn\').addEventListener(\'click\',function(){\n  var name=$(\'#supName\').value.trim();if(!name)return;\n  var rec={name:name,contact:$(\'#supContact\').value,phone:$(\'#supPhone\').value,email:$(\'#supEmail\').value,cats:$(\'#supCats\').value,address:$(\'#supAddr\').value,by_email:currentUser?currentUser.email:\'admin\'};\n  fetch(\'/api/suppliers\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify(rec)}).then(function(r){return r.json()}).then(function(d){if(d.id)rec.id=d.id}).catch(function(){});\n  suppliers.push({id:rec.id||Date.now(),name:rec.name,contact_person:rec.contact,categories:rec.cats,email:rec.email,phone:rec.phone});\n  toast(\'Supplier saved!\');renderSuppliers();[\'supName\',\'supContact\',\'supPhone\',\'supEmail\',\'supCats\',\'supAddr\'].forEach(function(i){$(\'#\'+i).value=\'\'});\n});\n$$(\'.atab\').forEach(function(tab){tab.addEventListener(\'click\',function(){$$(\'.atab\').forEach(function(t){t.classList.remove(\'active\')});tab.classList.add(\'active\');$(\'#aLogin\').style.display=tab.dataset.auth===\'login\'?\'block\':\'none\';$(\'#aSignup\').style.display=tab.dataset.auth===\'signup\'?\'block\':\'none\';})});\n$(\'#loginBtn\').addEventListener(\'click\',function(){\n  var email=$(\'#lEmail\').value.trim(),pw=$(\'#lPass\').value.trim(),type=$(\'#lType\').value;\n  if(!email||!pw){toast(\'Enter email and password\',false);return;}\n  fetch(\'/api/auth/login\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({email:email,password:pw,type:type})}).then(function(r){return r.json()}).then(function(d){\n    if(d.success){currentUser=Object.assign({},d.user,{type:d.type,is_master:Boolean(d.user.is_master)});$(\'#accBtn\').textContent=currentUser.name.split(\' \')[0];toast(\'Welcome \'+currentUser.name+\'!\');if(d.type===\'admin\')nav(\'admin\');else nav(\'profile\');}\n    else toast(d.message||\'Invalid credentials\',false);\n  }).catch(function(){toast(\'Connection error\',false)});\n});\n$(\'#signupBtn\').addEventListener(\'click\',function(){\n  var name=$(\'#sName\').value.trim(),email=$(\'#sEmail\').value.trim(),phone=$(\'#sPhone\').value.trim(),pw=$(\'#sPass\').value.trim();\n  var cpw=$(\'#sPassConfirm\')?$(\'#sPassConfirm\').value.trim():pw;\n  if(!name||!email||!pw){toast(\'Name, email and password required\',false);return;}\n  if(cpw&&pw!==cpw){toast(\'Passwords do not match\',false);return;}\n  fetch(\'/api/auth/signup\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({name:name,email:email,phone:phone,password:pw})}).then(function(r){return r.json()}).then(function(d){\n    if(d.success){toast(\'Account created! Signing you in...\');$(\'#lEmail\').value=email;$(\'#lPass\').value=pw;$(\'#lType\').value=\'user\';$(\'#loginBtn\').click();syncAll();}\n    else toast(d.message||\'Failed\',false);\n  }).catch(function(){toast(\'Connection error\',false)});\n});\n$(\'#dm\').addEventListener(\'click\',function(){$(\'#lEmail\').value=\'master@medicart.com\';$(\'#lPass\').value=\'master123\';$(\'#lType\').value=\'admin\';$(\'#loginBtn\').click()});\n$(\'#da\').addEventListener(\'click\',function(){$(\'#lEmail\').value=\'admin@medicart.com\';$(\'#lPass\').value=\'admin123\';$(\'#lType\').value=\'admin\';$(\'#loginBtn\').click()});\n$(\'#dc\').addEventListener(\'click\',function(){$(\'#lEmail\').value=\'john@example.com\';$(\'#lPass\').value=\'password123\';$(\'#lType\').value=\'user\';$(\'#loginBtn\').click()});\n$(\'#cBtn\').addEventListener(\'click\',function(){toast(\'Message sent! We will reply soon.\')});\nfunction syncAll(){\n  return Promise.all([fetch(\'/api/medicines\').then(function(r){return r.json()}),fetch(\'/api/categories\').then(function(r){return r.json()}),fetch(\'/api/suppliers\').then(function(r){return r.json()}),fetch(\'/api/orders\').then(function(r){return r.json()}),fetch(\'/api/prescriptions\').then(function(r){return r.json()}),fetch(\'/api/admin/stock\').then(function(r){return r.json()}),fetch(\'/api/users\').then(function(r){return r.json()}),fetch(\'/api/admins\').then(function(r){return r.json()})]).then(function(res){\n    if(Array.isArray(res[0])){MEDS.length=0;MEDS.push.apply(MEDS,res[0])}\n    if(Array.isArray(res[1])){CATS.length=0;CATS.push.apply(CATS,res[1])}\n    if(Array.isArray(res[2])){suppliers.length=0;suppliers.push.apply(suppliers,res[2])}\n    if(Array.isArray(res[3])){orders.length=0;orders.push.apply(orders,res[3])}\n    if(Array.isArray(res[4])){prescriptions.length=0;prescriptions.push.apply(prescriptions,res[4])}\n    if(Array.isArray(res[5])){STOCK.length=0;STOCK.push.apply(STOCK,res[5])}\n    if(Array.isArray(res[6])){dbUsers.length=0;dbUsers.push.apply(dbUsers,res[6])}\n    if(Array.isArray(res[7])){dbAdmins.length=0;dbAdmins.push.apply(dbAdmins,res[7])}\n  }).catch(function(){});\n}\nsyncAll().then(function(){renderHomeCats()});\nnav(\'home\');\n</script></body></html>'

def get_html():
    return HTML + JS


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

def run_server(start_port=PORT):
    init_db()
    server = None
    actual_port = start_port
    for p in range(start_port, start_port + 20):
        try:
            server = ReusableHTTPServer(('', p), PharmacyHandler)
            actual_port = p
            break
        except OSError:
            continue

    if not server:
        server = ReusableHTTPServer(('', 0), PharmacyHandler)
        actual_port = server.server_port

    url = 'http://localhost:{}/'.format(actual_port)
    print('=' * 60, flush=True)
    print('  MediCart Pharmacy - DBMS Project', flush=True)
    print('=' * 60, flush=True)
    print('  URL:      ' + url, flush=True)
    print('  Database: ' + DB_FILE, flush=True)
    print('', flush=True)
    print('  Schema: 10-table normalized SQLite (3NF)', flush=True)
    print('  Auth:   SHA-256 hashed passwords + audit log', flush=True)
    print('', flush=True)
    print('  Credentials:', flush=True)
    print('    Master Admin  master@medicart.com  / master123', flush=True)
    print('    Pharmacist    admin@medicart.com   / admin123', flush=True)
    print('    Customer      john@example.com     / password123', flush=True)
    print('', flush=True)
    print('  Press Ctrl+C to stop.', flush=True)
    print('=' * 60, flush=True)
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Server stopped.', flush=True)
        server.server_close()


if __name__ == '__main__':
    run_server()

