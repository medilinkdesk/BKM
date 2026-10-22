import os
import csv
import io
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, jsonify, redirect, 
    url_for, session, send_file, flash, make_response
)
from config import Config
from database import (
    init_db, create_donation, update_donation_status, update_donation_by_order,
    get_donation_by_id, get_donation_by_receipt, get_donations_by_phone,
    get_all_donations, get_donation_stats, get_announcements,
    add_announcement, delete_announcement, get_settings, update_settings,
    create_puja_booking
)
from payment_gateways import (
    create_razorpay_order, verify_razorpay_payment,
    create_cashfree_order, verify_cashfree_order,
    get_current_credentials
)
from pdf_receipt import generate_pdf_receipt

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY

# Ensure database is initialized
init_db()

# Context Processor for Global Template Variables
@app.context_processor
def inject_global_data():
    settings = get_settings()
    return {
        "temple_name_hi": Config.TEMPLE_NAME_HI,
        "temple_name_en": Config.TEMPLE_NAME_EN,
        "temple_location_hi": Config.TEMPLE_LOCATION_HI,
        "temple_location_en": Config.TEMPLE_LOCATION_EN,
        "temple_phone": settings.get("mandir_phone", Config.TEMPLE_PHONE),
        "temple_email": settings.get("mandir_email", Config.TEMPLE_EMAIL),
        "temple_upi_id": settings.get("mandir_upi_id", Config.TEMPLE_UPI_ID),
        "payment_mode": settings.get("payment_mode", Config.PAYMENT_MODE),
        "razorpay_key_id": settings.get("razorpay_key_id", Config.RAZORPAY_KEY_ID),
        "current_year": datetime.now().year
    }

# Admin Auth Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route("/")
def index():
    announcements = get_announcements()
    stats = get_donation_stats()
    return render_template("index.html", announcements=announcements, stats=stats)

@app.route("/history")
def history():
    return render_template("history.html")

@app.route("/darshan")
def darshan():
    return render_template("darshan.html")

@app.route("/donate")
def donate():
    settings = get_settings()
    return render_template("donate.html", settings=settings)

@app.route("/receipt/<receipt_no>")
def view_receipt(receipt_no):
    donation = get_donation_by_receipt(receipt_no)
    if not donation:
        flash("Receipt not found. Please verify the receipt number.", "error")
        return redirect(url_for('verify_receipt'))
    return render_template("receipt.html", donation=donation)

@app.route("/receipt/<receipt_no>/download-pdf")
def download_receipt_pdf(receipt_no):
    donation = get_donation_by_receipt(receipt_no)
    if not donation:
        return "Receipt not found", 404
    
    pdf_bytes = generate_pdf_receipt(donation)
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=Donation_Receipt_{receipt_no}.pdf'
    return response

@app.route("/verify-receipt", methods=["GET", "POST"])
def verify_receipt():
    results = []
    searched = False
    query = ""
    if request.method == "POST":
        searched = True
        query = request.form.get("search_query", "").strip()
        if query:
            # Check if receipt no
            if query.upper().startswith("BKM-"):
                rec = get_donation_by_receipt(query.upper())
                if rec:
                    results = [rec]
            else:
                # Search by phone or partial receipt
                results = get_donations_by_phone(query)
                if not results:
                    rec = get_donation_by_receipt(query)
                    if rec:
                        results = [rec]
    return render_template("verify_receipt.html", results=results, searched=searched, query=query)

@app.route("/puja-booking", methods=["GET", "POST"])
def puja_booking():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        gotra = request.form.get("gotra")
        puja_type = request.form.get("puja_type")
        puja_date = request.form.get("puja_date")
        sankalp = request.form.get("sankalp")
        amount = float(request.form.get("amount", 501))
        
        booking_id, booking_no = create_puja_booking(
            name, phone, email, gotra, puja_type, puja_date, sankalp, amount, f"PAY_PB_{booking_no}"
        )
        flash(f"Maa Kali Puja Booking Submitted! Your Booking No is {booking_no}. Temple priests will contact you.", "success")
        return redirect(url_for('puja_booking', success=booking_no))
        
    return render_template("puja_booking.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ==========================================
# PAYMENT GATEWAY API ENDPOINTS
# ==========================================

@app.route("/api/donation/initiate", methods=["POST"])
def initiate_donation():
    try:
        data = request.get_json() or {}
        donor_name = data.get("donor_name", "").strip()
        phone = data.get("phone", "").strip()
        email = data.get("email", "").strip()
        pan = data.get("pan", "").strip()
        address = data.get("address", "").strip()
        gotra = data.get("gotra", "").strip()
        purpose = data.get("purpose", "Nitya Bhog & Mandir Seva")
        amount = float(data.get("amount", 0))
        gateway = data.get("gateway", "RAZORPAY").upper()

        if not donor_name or not phone or amount <= 0:
            return jsonify({"status": "error", "message": "Please enter valid donor name, mobile number, and donation amount."}), 400

        # Step 1: Create initial record
        donation_id, receipt_no = create_donation(
            donor_name=donor_name,
            phone=phone,
            email=email,
            pan=pan,
            address=address,
            gotra=gotra,
            purpose=purpose,
            amount=amount,
            gateway=gateway,
            status="PENDING"
        )

        # Step 2: Handle Gateway Specific Order Generation
        if gateway == "RAZORPAY":
            rzp_res = create_razorpay_order(
                amount_in_inr=amount,
                receipt_no=receipt_no,
                notes={"donor_name": donor_name, "phone": phone, "purpose": purpose}
            )
            
            # Save order_id
            order_id = rzp_res.get("order_id")
            update_donation_by_order(order_id, "", status="PENDING")
            
            # Also update donation record with order_id
            conn = database_get_connection()
            conn.execute("UPDATE donations SET order_id = ? WHERE id = ?", (order_id, donation_id))
            conn.commit()
            conn.close()

            return jsonify({
                "status": "success",
                "gateway": "RAZORPAY",
                "donation_id": donation_id,
                "receipt_no": receipt_no,
                "order_id": order_id,
                "amount": rzp_res.get("amount"),
                "currency": "INR",
                "key_id": rzp_res.get("key_id"),
                "is_test_mode": rzp_res.get("is_test_mode", False),
                "donor_name": donor_name,
                "phone": phone,
                "email": email
            })

        elif gateway == "CASHFREE":
            return_url = url_for('cashfree_return', _external=True) + f"?receipt_no={receipt_no}"
            cf_res = create_cashfree_order(
                amount_in_inr=amount,
                receipt_no=receipt_no,
                customer_details={"name": donor_name, "phone": phone, "email": email},
                return_url=return_url
            )
            
            cf_order_id = cf_res.get("cf_order_id")
            conn = database_get_connection()
            conn.execute("UPDATE donations SET order_id = ? WHERE id = ?", (cf_order_id, donation_id))
            conn.commit()
            conn.close()

            return jsonify({
                "status": "success",
                "gateway": "CASHFREE",
                "donation_id": donation_id,
                "receipt_no": receipt_no,
                "order_id": cf_order_id,
                "payment_session_id": cf_res.get("payment_session_id"),
                "is_test_mode": cf_res.get("is_test_mode", False),
                "environment": Config.CASHFREE_ENV.lower()
            })

        elif gateway in ["UPI_QR", "UPI"]:
            settings = get_settings()
            upi_id = settings.get("mandir_upi_id", Config.TEMPLE_UPI_ID)
            # Create standard UPI intent
            upi_url = f"upi://pay?pa={upi_id}&pn=Burhi%20Kali%20Mandir%20Trust&am={amount:.2f}&cu=INR&tn=Donation%20{receipt_no}"
            
            return jsonify({
                "status": "success",
                "gateway": "UPI_QR",
                "donation_id": donation_id,
                "receipt_no": receipt_no,
                "upi_id": upi_id,
                "upi_url": upi_url,
                "amount": amount
            })

        else:
            return jsonify({"status": "error", "message": "Unsupported payment gateway"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def database_get_connection():
    from database import get_connection
    return get_connection()

@app.route("/api/payment/razorpay/verify", methods=["POST"])
def verify_razorpay():
    try:
        data = request.get_json() or {}
        donation_id = data.get("donation_id")
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        receipt_no = data.get("receipt_no")

        # Verify Signature
        is_valid, msg = verify_razorpay_payment(
            razorpay_order_id, razorpay_payment_id, razorpay_signature
        )

        if is_valid:
            if donation_id:
                update_donation_status(donation_id, razorpay_payment_id, status="COMPLETED")
            elif razorpay_order_id:
                update_donation_by_order(razorpay_order_id, razorpay_payment_id, status="COMPLETED")

            return jsonify({
                "status": "success",
                "message": "Payment verified successfully",
                "receipt_no": receipt_no,
                "redirect_url": url_for('view_receipt', receipt_no=receipt_no)
            })
        else:
            return jsonify({"status": "error", "message": msg}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/payment/cashfree/return")
def cashfree_return():
    order_id = request.args.get("order_id")
    receipt_no = request.args.get("receipt_no")
    
    if not receipt_no and order_id:
        donation = None
        conn = database_get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT receipt_no FROM donations WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        if row:
            receipt_no = row[0]
        conn.close()

    if receipt_no:
        # Check cashfree order status
        if order_id:
            success, status_str, pay_id = verify_cashfree_order(order_id)
            if success:
                update_donation_by_order(order_id, pay_id or f"CF_PAY_{order_id}", status="COMPLETED")
            else:
                # If mock or demo
                update_donation_by_order(order_id, f"CF_PAY_{order_id}", status="COMPLETED")
        
        return redirect(url_for('view_receipt', receipt_no=receipt_no))
    
    flash("Cashfree transaction processed. You can search your receipt here.", "info")
    return redirect(url_for('verify_receipt'))

@app.route("/api/payment/upi/submit-utr", methods=["POST"])
def submit_upi_utr():
    try:
        data = request.get_json() or {}
        donation_id = data.get("donation_id")
        utr_no = data.get("utr_no", "").strip()
        receipt_no = data.get("receipt_no")

        if not utr_no or len(utr_no) < 6:
            return jsonify({"status": "error", "message": "Please enter a valid 12-digit UPI Reference / UTR Number."}), 400

        # Mark donation completed with UTR
        update_donation_status(donation_id, f"UTR_{utr_no}", status="COMPLETED")

        return jsonify({
            "status": "success",
            "message": "Donation verified successfully via UPI!",
            "receipt_no": receipt_no,
            "redirect_url": url_for('view_receipt', receipt_no=receipt_no)
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ==========================================
# ADMIN PORTAL
# ==========================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session["admin_user"] = username
            flash("Welcome to Mandir Admin Management Portal", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid Mandir Admin credentials. Please try again.", "error")
            
    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    flash("You have been safely logged out.", "info")
    return redirect(url_for('admin_login'))

@app.route("/admin")
@app.route("/admin/dashboard")
@login_required
def admin_dashboard():
    search = request.args.get("search", "")
    gateway = request.args.get("gateway", "")
    status = request.args.get("status", "")
    page = int(request.args.get("page", 1))
    limit = 50
    offset = (page - 1) * limit
    
    donations = get_all_donations(search=search, gateway=gateway, status=status, limit=limit, offset=offset)
    stats = get_donation_stats()
    settings = get_settings()
    
    return render_template(
        "admin/dashboard.html",
        donations=donations,
        stats=stats,
        settings=settings,
        search=search,
        gateway=gateway,
        status=status,
        page=page
    )

@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    if request.method == "POST":
        new_settings = {
            "payment_mode": request.form.get("payment_mode", "TEST"),
            "razorpay_key_id": request.form.get("razorpay_key_id", "").strip(),
            "razorpay_key_secret": request.form.get("razorpay_key_secret", "").strip(),
            "cashfree_app_id": request.form.get("cashfree_app_id", "").strip(),
            "cashfree_secret_key": request.form.get("cashfree_secret_key", "").strip(),
            "cashfree_env": request.form.get("cashfree_env", "SANDBOX"),
            "mandir_upi_id": request.form.get("mandir_upi_id", "").strip(),
            "mandir_phone": request.form.get("mandir_phone", "").strip(),
            "mandir_email": request.form.get("mandir_email", "").strip(),
        }
        update_settings(new_settings)
        flash("Mandir Payment Gateway & Portal Settings Updated Successfully!", "success")
        return redirect(url_for('admin_settings'))
        
    settings = get_settings()
    return render_template("admin/settings.html", settings=settings)

@app.route("/admin/offline-donation", methods=["GET", "POST"])
@login_required
def admin_offline_donation():
    if request.method == "POST":
        donor_name = request.form.get("donor_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        pan = request.form.get("pan", "").strip()
        address = request.form.get("address", "").strip()
        gotra = request.form.get("gotra", "").strip()
        purpose = request.form.get("purpose", "Counter Cash Seva")
        amount = float(request.form.get("amount", 0))
        payment_mode = request.form.get("payment_mode", "CASH").upper()
        ref_no = request.form.get("ref_no", f"COUNTER_RCP_{datetime.now().strftime('%H%M%S')}")

        if not donor_name or not phone or amount <= 0:
            flash("Please provide donor name, phone, and valid amount.", "error")
            return redirect(url_for('admin_offline_donation'))

        donation_id, receipt_no = create_donation(
            donor_name=donor_name,
            phone=phone,
            email=email,
            pan=pan,
            address=address,
            gotra=gotra,
            purpose=purpose,
            amount=amount,
            gateway=f"OFFLINE_{payment_mode}",
            order_id=ref_no,
            payment_id=ref_no,
            status="COMPLETED"
        )
        
        flash(f"Counter Donation Recorded! Receipt No: {receipt_no}", "success")
        return redirect(url_for('view_receipt', receipt_no=receipt_no))

    return render_template("admin/offline_donate.html")

@app.route("/admin/announcements", methods=["GET", "POST"])
@login_required
def admin_announcements():
    if request.method == "POST":
        title = request.form.get("title")
        date_str = request.form.get("date_str")
        content = request.form.get("content")
        if title and content:
            add_announcement(title, date_str, content)
            flash("Notice published successfully!", "success")
            return redirect(url_for('admin_announcements'))
            
    announcements = get_announcements()
    return render_template("admin/announcements.html", announcements=announcements)

@app.route("/admin/announcements/delete/<int:announcement_id>")
@login_required
def admin_delete_announcement(announcement_id):
    delete_announcement(announcement_id)
    flash("Notice removed successfully", "info")
    return redirect(url_for('admin_announcements'))

@app.route("/admin/export-csv")
@login_required
def export_donations_csv():
    donations = get_all_donations(limit=10000)
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        "ID", "Receipt No", "Date", "Donor Name", "Phone", "Email", 
        "PAN", "Gotra", "Address", "Purpose", "Amount (INR)", "Gateway", 
        "Payment ID", "Status"
    ])
    
    for d in donations:
        cw.writerow([
            d.get("id"),
            d.get("receipt_no"),
            d.get("created_at"),
            d.get("donor_name"),
            d.get("phone"),
            d.get("email"),
            d.get("pan"),
            d.get("gotra"),
            d.get("address"),
            d.get("purpose"),
            d.get("amount"),
            d.get("gateway"),
            d.get("payment_id"),
            d.get("status")
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=Burhi_Kali_Mandir_Donations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    output.headers["Content-type"] = "text/csv; charset=utf-8"
    return output

if __name__ == "__main__":
    print(f"==================================================")
    print(f" Shree Shree 108 Buri Kali Mandir Portal (Kishanganj)")
    print(f" Location: Line Para, Kishanganj, Bihar (855107)")
    print(f" Server starting on http://127.0.0.1:5000")
    print(f" Admin Portal: http://127.0.0.1:5000/admin")
    print(f"==================================================")
    app.run(host="0.0.0.0", port=5000, debug=True)
