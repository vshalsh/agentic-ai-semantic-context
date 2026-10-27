"""Governed semantic context service. Standard-library educational implementation."""
import json
import sqlite3
from decimal import Decimal

class SemanticService:
    METRIC = {"metric_id": "net_revenue", "version": "1.0",
              "definition": "Paid invoices minus issued credits; drafts excluded",
              "currency": "USD"}
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE facts(tenant TEXT, period TEXT, doc_id TEXT, kind TEXT, amount TEXT, classification TEXT)")
        self.db.executemany("INSERT INTO facts VALUES(?,?,?,?,?,?)", [
            ("acme", "2026-10", "AC-I1", "paid_invoice", "1250.00", "public"),
            ("acme", "2026-10", "AC-I2", "paid_invoice", "500.00", "public"),
            ("acme", "2026-10", "AC-C1", "issued_credit", "200.00", "public"),
            ("acme", "2026-10", "AC-D1", "draft_invoice", "9000.00", "public"),
            ("other", "2026-10", "OT-I1", "paid_invoice", "9990.00", "public"),
            ("acme", "2026-11", "AC-I3", "paid_invoice", "300.00", "restricted"),
        ])
        self.audit = []

    def call(self, tool, args, context):
        # Trusted context comes from caller; never from model tool arguments.
        allowed = {"describe_metric": {"metric_id"},
                   "query_metric": {"metric_id", "period"},
                   "explain_lineage": {"metric_id", "period"}}
        if tool not in allowed or set(args) != allowed[tool]:
            return self._audit(tool, context, {"error": "invalid_arguments"})
        if args["metric_id"] != "net_revenue":
            return self._audit(tool, context, {"error": "unknown_metric"})
        if tool == "describe_metric":
            if "metric.read" not in context["scopes"]:
                return self._audit(tool, context, {"error": "missing_scope:metric.read"})
            return self._audit(tool, context, dict(self.METRIC))
        scope = "lineage.read" if tool == "explain_lineage" else "metric.read"
        if scope not in context["scopes"]:
            return self._audit(tool, context, {"error": "missing_scope:" + scope})
        rows = self.db.execute(
            "SELECT doc_id,kind,amount,classification FROM facts WHERE tenant=? AND period=?",
            (context["tenant"], args["period"])).fetchall()
        relevant = [r for r in rows if r[1] in ("paid_invoice", "issued_credit")]
        if any(r[3] == "restricted" for r in relevant) and "data.restricted" not in context["scopes"]:
            return self._audit(tool, context, {"error": "classification_denied"})
        if tool == "explain_lineage":
            result = {"metric_id": "net_revenue", "period": args["period"],
                      "source_ids": [r[0] for r in relevant], "definition_version": "1.0"}
        else:
            value = sum((Decimal(r[2]) if r[1] == "paid_invoice" else -Decimal(r[2])
                         for r in relevant), Decimal("0.00"))
            result = {"metric_id": "net_revenue", "period": args["period"],
                      "value": str(value.quantize(Decimal("0.01"))), "currency": "USD",
                      "definition_version": "1.0"}
        return self._audit(tool, context, result)

    def _audit(self, tool, context, result):
        self.audit.append({"tool": tool, "tenant": context["tenant"],
                           "outcome": result.get("error", "ok")})
        return result
