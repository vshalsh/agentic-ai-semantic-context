import unittest
from semantic import Context, SemanticService


class SemanticTests(unittest.TestCase):
    def setUp(self):
        self.s = SemanticService()
        self.s.seed()
        self.context = Context("alice", "acme", frozenset({"metric.read", "lineage.read"}))
        self.args = {"metric_id": "net_revenue", "period": "2026-10"}

    def tearDown(self):
        self.s.close()

    def test_revenue(self):
        self.assertEqual(self.s.call("query_metric", self.args, self.context)["value"], "1550.00")

    def test_lineage(self):
        sources = self.s.call("explain_lineage", self.args, self.context)["sources"]
        self.assertEqual({s["id"] for s in sources}, {"AC-I1", "AC-I2", "AC-C1"})

    def test_tenant_isolation(self):
        other = Context("bob", "other", frozenset({"metric.read"}))
        self.assertEqual(self.s.call("query_metric", self.args, other)["value"], "9990.00")

    def test_rejects_tenant_argument(self):
        self.assertEqual(self.s.call("query_metric",
            {**self.args, "tenant": "other"}, self.context)["error"], "invalid_arguments")

    def test_scope(self):
        limited = Context("alice", "acme", frozenset({"metric.read"}))
        self.assertEqual(self.s.call("explain_lineage", self.args, limited)["error"],
                         "missing_scope:lineage.read")

    def test_classification(self):
        self.assertEqual(self.s.call("query_metric",
            {**self.args, "period": "2026-11"}, self.context)["error"], "classification_denied")

    def test_restricted_permission(self):
        elevated = Context("alice", "acme", frozenset({"metric.read", "data.restricted"}))
        self.assertEqual(self.s.call("query_metric",
            {**self.args, "period": "2026-11"}, elevated)["value"], "300.00")

    def test_definition(self):
        self.assertEqual(self.s.call("describe_metric",
            {"metric_id": "net_revenue"}, self.context)["metric"]["version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
