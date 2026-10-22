import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "bkm_kishanganj_secret_key_108_kali_mata")
    DATABASE_PATH = BASE_DIR / "burhi_kali_mandir.db"
    RECEIPTS_DIR = BASE_DIR / "receipts"
    
    # Mandir Details
    TEMPLE_NAME_HI = "श्री श्री १०८ बूढ़ी काली मंदिर"
    TEMPLE_NAME_EN = "Shree Shree 108 Budhi Kali Mandir (Burhi Kali Mandir)"
    TEMPLE_LOCATION_HI = "लाइन पाड़ा, किशनगंज, बिहार - 855107"
    TEMPLE_LOCATION_EN = "Line Para, Kishanganj, Bihar - 855107"
    TEMPLE_REG_NO = "BR-KSG-BKM/1902-TRUST"
    TEMPLE_PHONE = "+91 6456 222108 / +91 94312 85510"
    TEMPLE_EMAIL = "sevadar@burhikalimandir.org"
    TEMPLE_UPI_ID = os.getenv("MANDIR_UPI_ID", "burhikalimandir@upi")
    
    # Payment Gateways Mode: 'TEST' (simulated/sandbox) or 'LIVE'
    PAYMENT_MODE = os.getenv("PAYMENT_MODE", "TEST")
    
    # Razorpay Credentials
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder_key")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder_secret")
    
    # Cashfree Credentials
    CASHFREE_APP_ID = os.getenv("CASHFREE_APP_ID", "TEST_CF_APP_ID")
    CASHFREE_SECRET_KEY = os.getenv("CASHFREE_SECRET_KEY", "TEST_CF_SECRET_KEY")
    CASHFREE_API_VERSION = "2023-08-01"
    CASHFREE_ENV = os.getenv("CASHFREE_ENV", "SANDBOX") # 'SANDBOX' or 'PRODUCTION'
    
    # Admin Credentials
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "kali108@ksg")
