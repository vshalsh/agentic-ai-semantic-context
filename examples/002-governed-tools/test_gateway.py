import unittest
from gateway import GovernedGateway, Principal


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.g = GovernedGateway()
        self.g.seed()
        self.admin = Principal("alice", "acme", frozenset({"invoice.read", "invoice.approve"}), 20000)

    def tearDown(self):
        self.g.close()

    def test_read(self):
        self.assertEqual(self.g.call("read_invoice", {"invoice_id": "A-100"}, self.admin)["status"], "ok")

    def test_tenant_isolation(self):
        self.assertEqual(self.g.call("read_invoice", {"invoice_id": "B-900"}, self.admin)["status"], "not_found")

    def test_rejects_untrusted_identity_fields(self):
        self.assertEqual(self.g.call("read_invoice", {"invoice_id": "A-100", "tenant": "other"},
                                     self.admin)["status"], "invalid_arguments")

    def test_scope(self):
        reader = Principal("bob", "acme", frozenset({"invoice.read"}), 0)
        self.assertEqual(self.g.call("approve_invoice",
            {"invoice_id": "A-100", "request_id": "1"}, reader)["status"], "missing_scope")

    def test_limit(self):
        self.assertEqual(self.g.call("approve_invoice",
            {"invoice_id": "A-200", "request_id": "2"}, self.admin)["status"], "approval_limit")

    def test_approve_and_retry(self):
        args = {"invoice_id": "A-100", "request_id": "3"}
        self.assertEqual(self.g.call("approve_invoice", args, self.admin)["status"], "ok")
        self.assertEqual(self.g.call("approve_invoice", args, self.admin)["status"], "ok")

    def test_idempotency_conflict(self):
        self.g.call("approve_invoice", {"invoice_id": "A-100", "request_id": "4"}, self.admin)
        self.assertEqual(self.g.call("approve_invoice",
            {"invoice_id": "A-200", "request_id": "4"}, self.admin)["status"], "idempotency_conflict")


if __name__ == "__main__":
    unittest.main()
