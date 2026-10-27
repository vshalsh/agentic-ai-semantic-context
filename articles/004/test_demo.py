import unittest
from server import SemanticService

class ContextTests(unittest.TestCase):
    def setUp(self):
        self.service = SemanticService()
        self.context = {"tenant": "acme", "scopes": {"metric.read", "lineage.read"}}
        self.args = {"metric_id": "net_revenue", "period": "2026-10"}

    def test_metric(self):
        self.assertEqual(self.service.call("query_metric", self.args, self.context)["value"], "1550.00")

    def test_lineage(self):
        self.assertEqual(set(self.service.call("explain_lineage", self.args, self.context)["source_ids"]),
                         {"AC-I1", "AC-I2", "AC-C1"})

    def test_tenant_spoof(self):
        self.assertEqual(self.service.call("query_metric",
            {**self.args, "tenant": "other"}, self.context)["error"], "invalid_arguments")

    def test_restricted(self):
        self.assertEqual(self.service.call("query_metric",
            {**self.args, "period": "2026-11"}, self.context)["error"], "classification_denied")

    def test_scope(self):
        ctx = {"tenant": "acme", "scopes": {"metric.read"}}
        self.assertEqual(self.service.call("explain_lineage", self.args, ctx)["error"],
                         "missing_scope:lineage.read")

if __name__ == "__main__":
    unittest.main()
