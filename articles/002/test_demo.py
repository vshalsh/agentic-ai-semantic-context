import unittest
from demo import ToolGateway, Context

class ToolTests(unittest.TestCase):
    def setUp(self):
        self.gateway = ToolGateway()
        self.admin = Context("alice", "acme", frozenset({"invoice.read", "invoice.approve"}), 200)

    def test_approve(self):
        self.assertEqual(self.gateway.call("approve_invoice", {"invoice_id": "A-100"}, self.admin)["status"], "ok")

    def test_scope(self):
        reader = Context("bob", "acme", frozenset({"invoice.read"}), 0)
        self.assertEqual(self.gateway.call("approve_invoice", {"invoice_id": "A-100"}, reader)["status"], "missing_scope")

    def test_tenant_isolation(self):
        self.assertEqual(self.gateway.call("read_invoice", {"invoice_id": "B-900"}, self.admin)["status"], "not_found")

    def test_rejects_model_supplied_tenant(self):
        self.assertEqual(self.gateway.call("read_invoice", {"invoice_id": "A-100", "tenant": "other"}, self.admin)["status"], "invalid_arguments")

    def test_limit(self):
        low = Context("alice", "acme", frozenset({"invoice.approve"}), 100)
        self.assertEqual(self.gateway.call("approve_invoice", {"invoice_id": "A-100"}, low)["status"], "approval_limit")

if __name__ == "__main__":
    unittest.main()
