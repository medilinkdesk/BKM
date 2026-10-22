import sqlite3
import datetime
import random
from config import Config

def get_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Donations Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            receipt_no TEXT UNIQUE NOT NULL,
            donor_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            pan TEXT,
            address TEXT,
            gotra TEXT,
            purpose TEXT NOT NULL,
            amount REAL NOT NULL,
            gateway TEXT NOT NULL,
            order_id TEXT,
            payment_id TEXT,
            status TEXT DEFAULT 'COMPLETED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Puja Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puja_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_no TEXT UNIQUE NOT NULL,
            devotee_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            gotra TEXT,
            puja_type TEXT NOT NULL,
            puja_date TEXT NOT NULL,
            sankalp_details TEXT,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'CONFIRMED',
            payment_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Announcements Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date_str TEXT NOT NULL,
            content TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Dynamic Settings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    seed_initial_data(conn)
    conn.close()

def generate_receipt_no():
    year = datetime.datetime.now().year
    random_digits = random.randint(10000, 99999)
    return f"BKM-{year}-{random_digits}"

def generate_booking_no():
    year = datetime.datetime.now().year
    random_digits = random.randint(1000, 9999)
    return f"BKMP-{year}-{random_digits}"

def seed_initial_data(conn):
    cursor = conn.cursor()
    
    # Initial settings
    default_settings = {
        "payment_mode": Config.PAYMENT_MODE,
        "razorpay_key_id": Config.RAZORPAY_KEY_ID,
        "razorpay_key_secret": Config.RAZORPAY_KEY_SECRET,
        "cashfree_app_id": Config.CASHFREE_APP_ID,
        "cashfree_secret_key": Config.CASHFREE_SECRET_KEY,
        "cashfree_env": Config.CASHFREE_ENV,
        "mandir_upi_id": Config.TEMPLE_UPI_ID,
        "mandir_phone": Config.TEMPLE_PHONE,
        "mandir_email": Config.TEMPLE_EMAIL,
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    # Check announcements
    cursor.execute("SELECT COUNT(*) FROM announcements")
    if cursor.fetchone()[0] == 0:
        announcements = [
            (
                "वार्षिक श्री श्री १०८ बूढ़ी काली पूजा महोत्सव एवं निशि पूजा",
                "दीपावली / कार्तिक अमावस्या",
                "किशनगंज लाइन पाड़ा में 120 वर्षों से निरंतर आयोजित हो रहे ऐतिहासिक वार्षिक महाकाली पूजनोत्सव में संपूर्ण सीमांचल व देश-विदेश से श्रद्धालु सादर आमंत्रित हैं। रात्रि १२ बजे से तांत्रिक व वैदिक निशि पूजा एवं महाप्रसाद वितरण।"
            ),
            (
                "प्रतिमा दान की पवित्र परंपरा - पंजीयन सूचना",
                "नियमित सूचना",
                "मां बूढ़ी काली के प्रति मन्नत पूर्ण होने पर प्रतिमा दान करने के लिए आगामी वर्षों की प्रतीक्षा सूची मंदिर कार्यालय अथवा ऑनलाइन संकल्प फॉर्म के माध्यम से दर्ज की जा सकती है।"
            ),
            (
                "मासिक अमावस्या महापूजन एवं सामूहिक शांति हवन",
                "प्रत्येक अमावस्या",
                "प्रत्येक कृष्ण पक्ष अमावस्या के पावन अवसर पर मंदिर परिसर में विशेष अभिषेक, हवन एवं शाम ७:०० बजे महाआरती संपन्न होती है।"
            )
        ]
        cursor.executemany(
            "INSERT INTO announcements (title, date_str, content) VALUES (?, ?, ?)",
            announcements
        )
    
    # Check sample initial donation if empty (for demonstration)
    cursor.execute("SELECT COUNT(*) FROM donations")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO donations 
            (receipt_no, donor_name, phone, email, pan, address, gotra, purpose, amount, gateway, order_id, payment_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-2 days'))
        ''', (
            "BKM-2024-10801",
            "आनंद प्रकाश वर्मा (Anand Prakash Verma)",
            "9835012345",
            "anand.verma@example.com",
            "ABCDE1234F",
            "लाइन पाड़ा, निकट गांधी चौक, किशनगंज",
            "कश्यप (Kashyap)",
            "नित्य भोग एवं महाप्रसाद सेवा (Nitya Bhog Seva)",
            2100.0,
            "RAZORPAY",
            "order_demo_10801",
            "pay_demo_kali_108",
            "COMPLETED"
        ))
        
        cursor.execute('''
            INSERT INTO donations 
            (receipt_no, donor_name, phone, email, pan, address, gotra, purpose, amount, gateway, order_id, payment_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '-1 day'))
        ''', (
            "BKM-2024-10802",
            "सुमन चक्रवर्ती (Suman Chakraborty)",
            "9431298765",
            "suman.c@example.com",
            "",
            "सिलीगुड़ी / किशनगंज (Siliguri)",
            "भारद्वाज (Bharadwaj)",
            "मंदिर जीर्णोद्धार एवं विकास कोष (Temple Renovation)",
            5100.0,
            "CASHFREE",
            "cf_order_10802",
            "cf_pay_kali_5100",
            "COMPLETED"
        ))
        
        cursor.execute('''
            INSERT INTO donations 
            (receipt_no, donor_name, phone, email, pan, address, gotra, purpose, amount, gateway, order_id, payment_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            "BKM-2024-10803",
            "राजेश कुमार साह (Rajesh Kumar Sah)",
            "9123456789",
            "rajesh.sah@example.com",
            "",
            "रुईधासा, किशनगंज (Ruidhasa, Kishanganj)",
            "शांडिल्य (Shandilya)",
            "दीप दान एवं अखंड ज्योति सेवा (Deep Daan Seva)",
            1100.0,
            "UPI_QR",
            "UPI_BKM_10803",
            "UTR_329482910482",
            "COMPLETED"
        ))
        
    conn.commit()

def create_donation(donor_name, phone, email, pan, address, gotra, purpose, amount, gateway, order_id=None, payment_id=None, status="PENDING"):
    conn = get_connection()
    cursor = conn.cursor()
    receipt_no = generate_receipt_no()
    
    cursor.execute('''
        INSERT INTO donations 
        (receipt_no, donor_name, phone, email, pan, address, gotra, purpose, amount, gateway, order_id, payment_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (receipt_no, donor_name, phone, email, pan, address, gotra, purpose, amount, gateway, order_id, payment_id, status))
    
    donation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return donation_id, receipt_no

def update_donation_status(donation_id, payment_id, status="COMPLETED"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE donations 
        SET payment_id = ?, status = ?
        WHERE id = ?
    ''', (payment_id, status, donation_id))
    conn.commit()
    conn.close()

def update_donation_by_order(order_id, payment_id, status="COMPLETED"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE donations 
        SET payment_id = ?, status = ?
        WHERE order_id = ?
    ''', (payment_id, status, order_id))
    conn.commit()
    conn.close()

def get_donation_by_id(donation_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM donations WHERE id = ?", (donation_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_donation_by_receipt(receipt_no):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM donations WHERE receipt_no = ?", (receipt_no.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_donations_by_phone(phone):
    conn = get_connection()
    cursor = conn.cursor()
    clean_phone = phone.strip()
    cursor.execute("SELECT * FROM donations WHERE phone = ? OR phone LIKE ? ORDER BY id DESC", 
                   (clean_phone, f"%{clean_phone}%"))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_donations(search="", gateway="", status="", limit=100, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM donations WHERE 1=1"
    params = []
    
    if search:
        query += " AND (donor_name LIKE ? OR phone LIKE ? OR receipt_no LIKE ? OR payment_id LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s])
        
    if gateway:
        query += " AND gateway = ?"
        params.append(gateway)
        
    if status:
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_donation_stats():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total successful donations
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM donations WHERE status = 'COMPLETED'")
    total_count, total_amount = cursor.fetchone()
    
    # Today's donations
    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM donations 
        WHERE status = 'COMPLETED' AND date(created_at) = date('now')
    """)
    today_count, today_amount = cursor.fetchone()
    
    # Gateways breakdown
    cursor.execute("""
        SELECT gateway, COUNT(*), COALESCE(SUM(amount), 0) 
        FROM donations WHERE status = 'COMPLETED'
        GROUP BY gateway
    """)
    gateway_stats = [dict(gateway=row[0], count=row[1], amount=row[2]) for row in cursor.fetchall()]
    
    conn.close()
    return {
        "total_count": total_count,
        "total_amount": total_amount,
        "today_count": today_count,
        "today_amount": today_amount,
        "gateways": gateway_stats
    }

def get_announcements():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM announcements WHERE is_active = 1 ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_announcement(title, date_str, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO announcements (title, date_str, content) VALUES (?, ?, ?)", (title, date_str, content))
    conn.commit()
    conn.close()

def delete_announcement(announcement_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    conn.commit()
    conn.close()

def get_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return settings

def update_settings(settings_dict):
    conn = get_connection()
    cursor = conn.cursor()
    for k, v in settings_dict.items():
        cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?", (k, v, v))
    conn.commit()
    conn.close()

def create_puja_booking(devotee_name, phone, email, gotra, puja_type, puja_date, sankalp_details, amount, payment_id):
    conn = get_connection()
    cursor = conn.cursor()
    booking_no = generate_booking_no()
    cursor.execute('''
        INSERT INTO puja_bookings 
        (booking_no, devotee_name, phone, email, gotra, puja_type, puja_date, sankalp_details, amount, payment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (booking_no, devotee_name, phone, email, gotra, puja_type, puja_date, sankalp_details, amount, payment_id))
    booking_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return booking_id, booking_no
