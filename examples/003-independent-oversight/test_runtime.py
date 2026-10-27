import tempfile
import unittest
from pathlib import Path
from runtime import Supervisor


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "test.sqlite")
        self.s = Supervisor(self.path)
        self.s.register_task("t", "acme", "alice")
        self.s.seed_invoice("acme", "I1")
        self.s.seed_invoice("acme", "I2")
        self.token = self.s.issue("t", "invoice.approve", "I1")
        self.args = dict(token=self.token, task_id="t", tenant="acme",
                         action="invoice.approve", resource="I1")

    def tearDown(self):
        self.s.close()
        self.tmp.cleanup()

    def test_approval_and_retry(self):
        self.assertTrue(self.s.execute(**self.args, request_id="1")["ok"])
        self.assertTrue(self.s.execute(**self.args, request_id="1")["ok"])
        self.assertEqual(len(self.s.audit()), 1)

    def test_stop(self):
        self.s.stop("t")
        self.assertEqual(self.s.execute(**self.args, request_id="2")["reason"], "task_stopped")
        with self.assertRaises(PermissionError):
            self.s.issue("t", "invoice.approve", "I2")

    def test_revoke(self):
        self.s.revoke(self.token)
        self.assertEqual(self.s.execute(**self.args, request_id="3")["reason"], "capability_inactive")

    def test_mismatch(self):
        self.assertEqual(self.s.execute(**{**self.args, "resource": "I2"},
                                        request_id="4")["reason"], "capability_mismatch")

    def test_tenant_isolation(self):
        self.assertEqual(self.s.execute(**{**self.args, "tenant": "other"},
                                        request_id="5")["reason"], "tenant_mismatch")

    def test_persistence(self):
        self.s.stop("t")
        self.s.close()
        self.s = Supervisor(self.path)
        self.assertEqual(self.s.execute(**self.args, request_id="6")["reason"], "task_stopped")

    def test_idempotency_conflict(self):
        self.s.execute(**self.args, request_id="7")
        self.assertEqual(self.s.execute(**{**self.args, "resource": "I2"},
                                        request_id="7")["reason"], "idempotency_conflict")


if __name__ == "__main__":
    unittest.main()
