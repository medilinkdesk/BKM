import unittest
from app import app
from config import Config

class AdminTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_admin_flow(self):
        # 1. Access dashboard without login -> redirected to login
        res = self.app.get("/admin/dashboard", follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        print("[PASS] Unauthenticated access redirects to login")

        # 2. Login with correct credentials
        login_res = self.app.post("/admin/login", data={
            "username": Config.ADMIN_USERNAME,
            "password": Config.ADMIN_PASSWORD
        }, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Admin Portal", login_res.data)
        print("[PASS] Admin login succeeded")

        # 3. View Settings
        settings_res = self.app.get("/admin/settings")
        self.assertEqual(settings_res.status_code, 200)
        self.assertIn(b"Razorpay API Credentials", settings_res.data)
        print("[PASS] Admin settings page accessible")

        # 4. View Offline Counter Donation form
        offline_res = self.app.get("/admin/offline-donation")
        self.assertEqual(offline_res.status_code, 200)
        print("[PASS] Admin offline donation form accessible")

        # 5. Export CSV
        csv_res = self.app.get("/admin/export-csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.content_type, "text/csv; charset=utf-8")
        self.assertIn(b"Receipt No", csv_res.data)
        print(f"[PASS] CSV Export successful ({len(csv_res.data)} bytes)")

if __name__ == "__main__":
    unittest.main()
