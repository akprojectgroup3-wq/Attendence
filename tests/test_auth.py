"""Automated tests for Administrator Authentication & Session Security.

Verifies:
- Test 1: Admin login succeeds with valid credentials.
- Test 2: Invalid login is rejected.
- Test 15: Protected routes require authentication.
"""

import unittest
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from werkzeug.security import generate_password_hash

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app
from services.storage_service import init_storage, sync_admin_password_from_env, verify_user


class TestAuthentication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_storage()
        cls.client = app.test_client()
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

    def test_01_verify_user_storage_function(self):
        """Test underlying user password verification logic with hashed credentials."""
        # Valid admin credentials
        user = verify_user("admin", "admin123")
        self.assertIsNotNone(user, "Default admin user should verify successfully.")
        self.assertEqual(user.get("role"), "admin")

        # Invalid password
        invalid_user = verify_user("admin", "wrongpassword")
        self.assertIsNone(invalid_user, "Invalid password should return None.")

        # Non-existent user
        non_existent = verify_user("nonexistent_user", "admin123")
        self.assertIsNone(non_existent, "Non-existent user should return None.")

    def test_environment_password_updates_existing_admin(self):
        with TemporaryDirectory() as temp_dir:
            users_path = Path(temp_dir) / "users.json"
            users_path.write_text(json.dumps({
                "admin": {
                    "username": "admin",
                    "password_hash": generate_password_hash("old-password"),
                    "role": "admin"
                }
            }), encoding="utf-8")

            with patch("services.storage_service.USERS_JSON", users_path):
                with patch.dict(os.environ, {"ADMIN_PASSWORD": "render-password"}):
                    self.assertTrue(sync_admin_password_from_env())
                    self.assertIsNotNone(verify_user("admin", "render-password"))
                    self.assertIsNone(verify_user("admin", "old-password"))

    def test_02_admin_login_endpoint_success(self):
        """Test Case 1: Administrator login succeeds with valid credentials."""
        response = self.client.post("/login", data={
            "username": "admin",
            "password": "admin123"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        # Should be redirected to dashboard
        self.assertIn(b"Classroom Attendance Overview", response.data)
        self.assertIn(b"Sign Out", response.data)

    def test_03_admin_login_endpoint_failure(self):
        """Test Case 2: Invalid login is rejected."""
        fresh_client = app.test_client()
        response = fresh_client.post("/login", data={
            "username": "admin",
            "password": "wrong_password_999"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)

    def test_04_protected_routes_require_authentication(self):
        """Test Case 15: Protected pages require authentication."""
        # Fresh unauthenticated client
        unauth_client = app.test_client()

        protected_urls = [
            "/dashboard",
            "/students",
            "/register-face",
            "/live-attendance",
            "/attendance",
            "/reports",
            "/settings"
        ]

        for url in protected_urls:
            resp = unauth_client.get(url, follow_redirects=False)
            self.assertEqual(
                resp.status_code, 302,
                f"Unauthenticated access to {url} should redirect (302) to login."
            )
            self.assertIn("/login", resp.headers.get("Location", ""))


if __name__ == "__main__":
    unittest.main()
