import unittest
from app import app
from database import get_donation_by_receipt

class MandirPortalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_pages_load(self):
        routes = ["/", "/history", "/darshan", "/donate", "/verify-receipt", "/puja-booking", "/gallery", "/contact", "/admin/login"]
        for r in routes:
            res = self.app.get(r)
            self.assertEqual(res.status_code, 200, f"Route {r} failed with status {res.status_code}")
            print(f"[PASS] Route {r} loaded successfully (200 OK)")

    def test_donation_initiate_razorpay(self):
        payload = {
            "donor_name": "Rahul Kumar Jha",
            "phone": "9876543210",
            "email": "rahul.jha@example.com",
            "pan": "ABCDE1234F",
            "address": "Gandhi Chowk, Kishanganj",
            "gotra": "Kashyap",
            "purpose": "Nitya Bhog Seva",
            "amount": 1100,
            "gateway": "RAZORPAY"
        }
        res = self.app.post("/api/donation/initiate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("receipt_no", data)
        self.assertIn("order_id", data)
        print(f"[PASS] Razorpay Order: Receipt={data['receipt_no']}, OrderID={data['order_id']}")

        # Verify Payment
        v_res = self.app.post("/api/payment/razorpay/verify", json={
            "donation_id": data["donation_id"],
            "razorpay_order_id": data["order_id"],
            "razorpay_payment_id": "pay_test_rzp_mock_123",
            "razorpay_signature": "mock_sig",
            "receipt_no": data["receipt_no"]
        })
        self.assertEqual(v_res.status_code, 200)
        v_data = v_res.get_json()
        self.assertEqual(v_data["status"], "success")
        print(f"[PASS] Razorpay verified successfully for {data['receipt_no']}")

        # Test Receipt Page
        rec_res = self.app.get(f"/receipt/{data['receipt_no']}")
        self.assertEqual(rec_res.status_code, 200)
        print(f"[PASS] Receipt view rendered for {data['receipt_no']}")

        # Test PDF download
        pdf_res = self.app.get(f"/receipt/{data['receipt_no']}/download-pdf")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.content_type, "application/pdf")
        self.assertGreater(len(pdf_res.data), 1000)
        print(f"[PASS] PDF receipt generated and downloaded ({len(pdf_res.data)} bytes)")

    def test_donation_initiate_cashfree(self):
        payload = {
            "donor_name": "Sourav Ganguly",
            "phone": "9123456789",
            "email": "sourav@example.com",
            "pan": "",
            "address": "Siliguri / Kishanganj",
            "gotra": "Shandilya",
            "purpose": "Temple Renovation Fund",
            "amount": 2100,
            "gateway": "CASHFREE"
        }
        res = self.app.post("/api/donation/initiate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("payment_session_id", data)
        print(f"[PASS] Cashfree Order: Session ID={data['payment_session_id']}")

    def test_donation_initiate_upi(self):
        payload = {
            "donor_name": "Mohan Das",
            "phone": "9431200000",
            "email": "",
            "pan": "",
            "address": "Line Para, Kishanganj",
            "gotra": "Bharadwaj",
            "purpose": "Deep Daan Seva",
            "amount": 501,
            "gateway": "UPI_QR"
        }
        res = self.app.post("/api/donation/initiate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("upi_url", data)
        print(f"[PASS] UPI QR: UPI URL={data['upi_url']}")

        # Submit UTR
        utr_res = self.app.post("/api/payment/upi/submit-utr", json={
            "donation_id": data["donation_id"],
            "utr_no": "329482910482",
            "receipt_no": data["receipt_no"]
        })
        self.assertEqual(utr_res.status_code, 200)
        u_data = utr_res.get_json()
        self.assertEqual(u_data["status"], "success")
        print(f"[PASS] UPI UTR submitted and receipt verified for {data['receipt_no']}")

if __name__ == "__main__":
    unittest.main()
