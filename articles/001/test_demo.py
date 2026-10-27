import unittest
from datetime import datetime, timedelta, timezone
from demo import Gateway, Grant

class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.gateway = Gateway()
        self.grant = Grant("alice", "acme", "task-1", "invoice.approve", "INV-1", 200,
                           datetime.now(timezone.utc) + timedelta(minutes=5))

    def test_approved(self):
        self.assertTrue(self.gateway.approve(self.grant, "acme", "task-1", "INV-1")["allowed"])

    def test_revoked(self):
        self.grant.revoked = True
        self.assertEqual(self.gateway.approve(self.grant, "acme", "task-1", "INV-1")["reason"], "grant_inactive")

    def test_amount_limit(self):
        self.grant.max_amount = 100
        self.assertEqual(self.gateway.approve(self.grant, "acme", "task-1", "INV-1")["reason"], "amount_limit")

    def test_tenant_spoof(self):
        self.assertEqual(self.gateway.approve(self.grant, "other", "task-1", "INV-1")["reason"], "delegation_mismatch")

if __name__ == "__main__":
    unittest.main()
