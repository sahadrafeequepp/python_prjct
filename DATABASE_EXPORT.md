# 🏥 MediCart Pharmacy Management System — Database Stored Data
**Target DBMS:** SQLite 3 (`pharmacy_dbms.db`)  
**Export Generated:** 2026-09-06 22:08:20  
**Normalization:** 3NF (Third Normal Form) | **Total Tables:** 10 | **Active Views:** 6  

---

## 📑 Table of Contents
1. [categories](#1-categories)
2. [admins](#2-admins)
3. [users](#3-users)
4. [suppliers](#4-suppliers)
5. [medicines](#5-medicines)
6. [stock_batches](#6-stock_batches)
7. [orders](#7-orders)
8. [order_items](#8-order_items)
9. [prescriptions](#9-prescriptions)
10. [audit_log](#10-audit_log)
11. [SQL Analytical Views](#11-sql-analytical-views)

---

### 1. `categories`
**Total records:** 6  

| ID | Slug | Name | Icon | Description |
| --- | --- | --- | --- | --- |
| 1 | pain | Pain Relief | 💊 | Analgesics, antipyretics, and anti-inflammatory drugs |
| 2 | antibiotics | Antibiotics | 🦠 | Prescription antibacterial and anti-infective medications |
| 3 | vitamins | Vitamins & Supps | 💉 | Essential multivitamins, minerals, and daily supplements |
| 4 | skincare | Skin Care | 🧴 | Dermatological creams, lotions, and soothing gels |
| 5 | babycare | Baby Care | 🍼 | Pediatric medicines, baby nutrition, and infant care |
| 6 | personalcare | Personal Hygiene | 🧼 | Hand hygiene, antiseptics, and personal sanitizers |

---

### 2. `admins`
**Total records:** 2  

| ID | Name | Email | Phone | Role | Is Master | Created At |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Master Administrator | master@medicart.com | +91 99000 00000 | Master Admin | 1 | 2026-08-01 10:00:00 |
| 2 | Dr. Kavya Suresh | admin@medicart.com | +91 98450 99887 | Head Pharmacist | 0 | 2026-08-05 11:30:00 |

---

### 3. `users`
**Total records:** 2  

| ID | Name | Email | Phone | Address | Created At |
| --- | --- | --- | --- | --- | --- |
| 1 | John Doe | john@example.com | +91 98765 43210 | 44, Lotus Residency, MG Road, Kochi, Kerala 682016 | 2026-08-10 14:15:00 |
| 2 | Priya Sharma | priya@example.com | +91 98412 34567 | 12B, Marine Drive Towers, Ernakulam, Kerala 682011 | 2026-08-15 09:45:00 |

---

### 4. `suppliers`
**Total records:** 3  

| ID | Name | Contact Person | Phone | Email | Categories | Address |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | MedSupply Co. | Suresh Nair | +91 98450 11223 | suresh@medsupply.in | Pain Relief, Antibiotics | Plot 18, Industrial Estate, Kochi, Kerala |
| 2 | Wellness Distributors | Priya Menon | +91 97460 22110 | priya@wellnessdist.in | Vitamins & Supps, Hygiene | 45, Commercial Road, Kozhikode, Kerala |
| 3 | CarePlus Traders | Arun Das | +91 94470 33987 | arun@careplustraders.in | Skin Care, Baby Care | 8, Technopark Avenue, Thiruvananthapuram, Kerala |

---

### 5. `medicines`
**Total records:** 12  

| ID | Medicine Name | Cat ID | Price (₹) | Rating | Reviews | Stock | Rx Required | Manufacturer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Paracetamol 500mg | 1 | 45.0 | 4.8 | 120 | 237 | 0 | Apex Health |
| 2 | Ibuprofen 400mg | 1 | 60.0 | 4.7 | 98 | 180 | 0 | Abbott Healthcare |
| 3 | Amoxicillin 250mg | 2 | 120.0 | 4.6 | 88 | 58 | 1 | Sun Pharma |
| 4 | Azithromycin 500mg (3 Tabs) | 2 | 150.0 | 4.5 | 41 | 0 | 1 | Cipla Ltd |
| 5 | Vitamin C 1000mg Effervescent | 3 | 180.0 | 4.9 | 210 | 149 | 0 | Redoxon Labs |
| 6 | Adult Multivitamin Gummies | 3 | 220.0 | 4.8 | 134 | 74 | 0 | NutraLife |
| 7 | Soothing Aloe Vera Gel 200ml | 4 | 210.0 | 4.5 | 64 | 89 | 0 | Nature Care |
| 8 | Moisturizing Sunscreen SPF 50 | 4 | 280.0 | 4.7 | 82 | 120 | 0 | DermaShield |
| 9 | Baby Colic Relief Drops 30ml | 5 | 160.0 | 4.4 | 52 | 39 | 0 | Himalaya Baby |
| 10 | Zinc Oxide Diaper Rash Cream 50g | 5 | 140.0 | 4.6 | 59 | 54 | 0 | Sebamed Baby |
| 11 | Antibacterial Hand Wash 250ml | 6 | 95.0 | 4.3 | 73 | 199 | 0 | Dettol Herbal |
| 12 | Antiseptic Disinfectant 500ml | 6 | 175.0 | 4.6 | 91 | 15 | 0 | LifeGuard Care |

---

### 6. `stock_batches`
**Total records:** 12  

| ID | Med ID | Batch No | Quantity | Expiry Date | Status | Received Date | Supplier ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 12 | 12 | BTC-2026-012 | 15 | 2026-09-18 | expiring | 2026-08-18 | 2 |
| 4 | 4 | BTC-2026-004 | 0 | 2026-09-25 | out | 2026-08-05 | 1 |
| 9 | 9 | BTC-2026-009 | 40 | 2026-10-15 | low | 2026-08-15 | 3 |
| 3 | 3 | BTC-2026-003 | 60 | 2026-11-10 | low | 2026-08-05 | 1 |
| 5 | 5 | BTC-2026-005 | 150 | 2027-04-18 | ok | 2026-08-10 | 2 |
| 10 | 10 | BTC-2026-010 | 55 | 2027-05-30 | ok | 2026-08-15 | 3 |
| 6 | 6 | BTC-2026-006 | 75 | 2027-06-30 | ok | 2026-08-10 | 2 |
| 7 | 7 | BTC-2026-007 | 90 | 2027-08-15 | ok | 2026-08-12 | 3 |
| 8 | 8 | BTC-2026-008 | 120 | 2027-09-20 | ok | 2026-08-12 | 3 |
| 2 | 2 | BTC-2026-002 | 180 | 2027-10-20 | ok | 2026-08-01 | 1 |
| 1 | 1 | BTC-2026-001 | 240 | 2027-11-15 | ok | 2026-08-01 | 1 |
| 11 | 11 | BTC-2026-011 | 200 | 2028-01-10 | ok | 2026-08-18 | 2 |

---

### 7. `orders`
**Total records:** 5  

| Order ID | Customer Email | Date | Total (₹) | Status | Recipient | Phone | Time Slot | Payment |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ORD-2026-005 | john@example.com | 2026-09-06 | 240.0 | Placed | John Doe | +91 98765 43210 | Evening (4 PM - 8 PM) | Cash on Delivery |
| ORD-2026-004 | priya@example.com | 2026-09-02 | 350.0 | Confirmed | Priya Sharma | +91 98412 34567 | Morning (9 AM - 12 PM) | UPI / Online |
| ORD-2026-003 | priya@example.com | 2026-08-29 | 205.0 | Shipped | Priya Sharma | +91 98412 34567 | Afternoon (1 PM - 4 PM) | Cash on Delivery |
| ORD-2026-002 | john@example.com | 2026-08-22 | 315.0 | Delivered | John Doe | +91 98765 43210 | Evening (4 PM - 8 PM) | Card |
| ORD-2026-001 | john@example.com | 2026-08-15 | 270.0 | Delivered | John Doe | +91 98765 43210 | Morning (9 AM - 12 PM) | UPI / Online |

---

### 8. `order_items`
**Total records:** 9  

| ID | Order ID | Med ID | Quantity | Unit Price (₹) |
| --- | --- | --- | --- | --- |
| 1 | ORD-2026-001 | 1 | 2 | 45.0 |
| 2 | ORD-2026-001 | 5 | 1 | 180.0 |
| 3 | ORD-2026-002 | 11 | 1 | 95.0 |
| 4 | ORD-2026-002 | 6 | 1 | 220.0 |
| 5 | ORD-2026-003 | 9 | 1 | 160.0 |
| 6 | ORD-2026-003 | 1 | 1 | 45.0 |
| 7 | ORD-2026-004 | 7 | 1 | 210.0 |
| 8 | ORD-2026-004 | 10 | 1 | 140.0 |
| 9 | ORD-2026-005 | 3 | 2 | 120.0 |

---

### 9. `prescriptions`
**Total records:** 3  

| ID | File Name | Patient Name | Doctor Name | Date | Status | Order ID | Customer Email |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | rx_respiratory_care.pdf | Priya Sharma | Dr. Kavya Suresh | 2026-09-05 | Pending |  | priya@example.com |
| 2 | rx_pediatric_colic.pdf | Baby Maya | Dr. Paul Mathew | 2026-08-28 | Verified | ORD-2026-003 | priya@example.com |
| 1 | rx_amoxicillin_john.pdf | John Doe | Dr. Kavya Suresh | 2026-08-20 | Verified | ORD-2026-001 | john@example.com |

---

### 10. `audit_log`
**Total records:** 10  

| ID | Action | Entity | Entity ID | User Email | Role | Timestamp | Details |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | SYSTEM_INIT | database | 0 | system | system | 2026-08-01 00:00:00 | Initialized 10-table normalized 3NF schema with 6 views, 5 triggers, 10 indexes. |
| 9 | CREATE_ORDER | orders | ORD-2026-005 | john@example.com | customer | 2026-09-06 22:05:19 | Order total: ₹240.0 for John Doe |
| 8 | CREATE_ORDER | orders | ORD-2026-004 | priya@example.com | customer | 2026-09-06 22:05:19 | Order total: ₹350.0 for Priya Sharma |
| 7 | CREATE_ORDER | orders | ORD-2026-003 | priya@example.com | customer | 2026-09-06 22:05:19 | Order total: ₹205.0 for Priya Sharma |
| 6 | CREATE_ORDER | orders | ORD-2026-002 | john@example.com | customer | 2026-09-06 22:05:19 | Order total: ₹315.0 for John Doe |
| 5 | CREATE_ORDER | orders | ORD-2026-001 | john@example.com | customer | 2026-09-06 22:05:19 | Order total: ₹270.0 for John Doe |
| 4 | USER_SIGNUP | users | 2 | priya@example.com | customer | 2026-09-06 22:05:19 | New customer registration: Priya Sharma |
| 3 | USER_SIGNUP | users | 1 | john@example.com | customer | 2026-09-06 22:05:19 | New customer registration: John Doe |
| 2 | CREATE_ADMIN | admins | 2 | admin@medicart.com | admin | 2026-09-06 22:05:19 | Role: Head Pharmacist (Master=0) |
| 1 | CREATE_ADMIN | admins | 1 | master@medicart.com | master | 2026-09-06 22:05:19 | Role: Master Admin (Master=1) |

---

## 11. SQL Analytical Views

### View: `v_sales_by_category`
| Category | Orders | Units Sold | Revenue (₹) |
|---|---|---|---|
| Vitamins & Supps | 2 | 2 | ₹400.00 |
| Baby Care | 2 | 2 | ₹300.00 |
| Antibiotics | 1 | 2 | ₹240.00 |
| Skin Care | 1 | 1 | ₹210.00 |
| Pain Relief | 2 | 3 | ₹135.00 |
| Personal Hygiene | 1 | 1 | ₹95.00 |


### View: `v_stock_alerts`
| Batch No | Medicine | Category | Stock | Expiry Date | Status | Supplier |
|---|---|---|---|---|---|---|
| BTC-2026-012 | Antiseptic Disinfectant 500ml | Personal Hygiene | 15 | 2026-09-18 | expiring | Wellness Distributors |
| BTC-2026-004 | Azithromycin 500mg (3 Tabs) | Antibiotics | 0 | 2026-09-25 | out | MedSupply Co. |
| BTC-2026-009 | Baby Colic Relief Drops 30ml | Baby Care | 40 | 2026-10-15 | low | CarePlus Traders |
| BTC-2026-003 | Amoxicillin 250mg | Antibiotics | 60 | 2026-11-10 | low | MedSupply Co. |

