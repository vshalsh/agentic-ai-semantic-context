import tempfile
import unittest
from pathlib import Path
from authority import AuthorityService


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "test.sqlite")
        self.service = AuthorityService(self.path)
        self.service.seed_invoice("acme", "I1", 12000)
        self.service.seed_invoice("acme", "I2", 50000)
        self.token = self.service.delegate(sponsor="alice", tenant="acme", task_id="t",
                                           resource="I1", limit_cents=20000)
        self.args = dict(token=self.token, tenant="acme", task_id="t", resource="I1")

    def tearDown(self):
        self.service.close()
        self.tmp.cleanup()

    def test_authorized_and_idempotent(self):
        first = self.service.approve(**self.args, request_id="op1")
        again = self.service.approve(**self.args, request_id="op1")
        self.assertTrue(first.allowed)
        self.assertEqual(first, again)
        self.assertEqual(len(self.service.audit()), 1)

    def test_revocation(self):
        self.service.revoke(self.token)
        self.assertEqual(self.service.approve(**self.args, request_id="op2").reason, "grant_inactive")

    def test_cross_tenant(self):
        self.assertEqual(self.service.approve(**{**self.args, "tenant": "other"},
                                              request_id="op3").reason, "delegation_mismatch")

    def test_resource_binding(self):
        self.assertEqual(self.service.approve(**{**self.args, "resource": "I2"},
                                              request_id="op4").reason, "delegation_mismatch")

    def test_idempotency_conflict(self):
        self.service.approve(**self.args, request_id="op5")
        conflict = self.service.approve(**{**self.args, "resource": "I2"}, request_id="op5")
        self.assertEqual(conflict.reason, "idempotency_conflict")

    def test_persists_after_reopen(self):
        self.service.approve(**self.args, request_id="op6")
        self.service.close()
        self.service = AuthorityService(self.path)
        self.assertEqual(self.service.invoice_status("acme", "I1"), "approved")
        self.assertEqual(len(self.service.audit()), 1)


if __name__ == "__main__":
    unittest.main()
