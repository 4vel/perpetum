import unittest

from app.auth import AuthManager
from app.config import Settings


class AuthManagerTest(unittest.TestCase):
    def setUp(self):
        self.auth = AuthManager(
            Settings(
                auth_username="admin",
                auth_password="correct horse battery staple",
                auth_secret="a" * 48,
                auth_session_hours=1,
            )
        )

    def test_authenticates_and_verifies_signed_session(self):
        self.assertTrue(self.auth.configured)
        self.assertTrue(self.auth.authenticate("admin", "correct horse battery staple"))
        token = self.auth.create_session("admin")
        self.assertEqual(self.auth.verify_session(token), "admin")

    def test_rejects_wrong_password_and_tampered_session(self):
        self.assertFalse(self.auth.authenticate("admin", "wrong"))
        token = self.auth.create_session("admin")
        self.assertIsNone(self.auth.verify_session(token + "tampered"))

    def test_supports_non_ascii_credentials(self):
        auth = AuthManager(
            Settings(
                auth_username="администратор",
                auth_password="надёжный пароль",
                auth_secret="с" * 48,
            )
        )
        self.assertTrue(auth.authenticate("администратор", "надёжный пароль"))
        self.assertFalse(auth.authenticate("администратор", "неверный пароль"))
