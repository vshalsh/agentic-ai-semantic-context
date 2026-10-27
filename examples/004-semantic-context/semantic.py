"""Governed metric semantics, row-level tenant isolation and reproducible lineage."""
from __future__ import annotations
import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import FrozenSet


@dataclass(frozen=True)
class Context:
    subject: str
    tenant: str
    scopes: FrozenSet[str]


class SemanticService:
    """The model selects tools; this service owns definitions and policy."""

    DEFINITION = {
        "id": "net_revenue",
        "version": "1.0.0",
        "label": "Net revenue",
        "formula": "SUM(paid_invoice) - SUM(issued_credit)",
        "excludes": ["draft_invoice"],
        "currency": "USD",
        "grain": "tenant, month",
    }
    SCHEMAS = {
        "describe_metric": {"metric_id"},
        "query_metric": {"metric_id", "period"},
        "explain_lineage": {"metric_id", "period"},
    }

    def __init__(self, db_path=":memory:"):
        self.db = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS facts(
                tenant TEXT NOT NULL, period TEXT NOT NULL,
                source_id TEXT NOT NULL, kind TEXT NOT NULL,
                amount_cents INTEGER NOT NULL, classification TEXT NOT NULL,
                PRIMARY KEY(tenant,source_id));
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                subject TEXT NOT NULL, tenant TEXT NOT NULL,
                tool TEXT NOT NULL, outcome TEXT NOT NULL);
        """)

    def seed(self):
        with self.lock:
            self.db.executemany("INSERT OR IGNORE INTO facts VALUES (?,?,?,?,?,?)", [
                ("acme", "2026-10", "AC-I1", "paid_invoice", 125000, "internal"),
                ("acme", "2026-10", "AC-I2", "paid_invoice", 50000, "internal"),
                ("acme", "2026-10", "AC-C1", "issued_credit", 20000, "internal"),
                ("acme", "2026-10", "AC-D1", "draft_invoice", 900000, "internal"),
                ("other", "2026-10", "OT-I1", "paid_invoice", 999000, "internal"),
                ("acme", "2026-11", "AC-I3", "paid_invoice", 30000, "restricted"),
            ])

    def tools(self):
        return [{"name": name, "arguments": sorted(fields)}
                for name, fields in self.SCHEMAS.items()]

    def call(self, tool: str, arguments: dict, context: Context) -> dict:
        with self.lock:
            if tool not in self.SCHEMAS or not isinstance(arguments, dict) or (
                set(arguments) != self.SCHEMAS.get(tool)) or any(
                    not isinstance(v, str) or not v for v in arguments.values()):
                return self._audit(tool, context, {"error": "invalid_arguments"})
            if arguments["metric_id"] != self.DEFINITION["id"]:
                return self._audit(tool, context, {"error": "unknown_metric"})
            scope = "lineage.read" if tool == "explain_lineage" else "metric.read"
            if scope not in context.scopes:
                return self._audit(tool, context, {"error": "missing_scope:" + scope})
            if tool == "describe_metric":
                return self._audit(tool, context, {"metric": dict(self.DEFINITION)})
            rows = self.db.execute(
                "SELECT * FROM facts WHERE tenant=? AND period=? AND kind IN (?,?) ORDER BY source_id",
                (context.tenant, arguments["period"], "paid_invoice", "issued_credit")
            ).fetchall()
            if any(r["classification"] == "restricted" for r in rows) and (
                    "data.restricted" not in context.scopes):
                return self._audit(tool, context, {"error": "classification_denied"})
            if tool == "explain_lineage":
                result = {"metric_id": self.DEFINITION["id"],
                          "definition_version": self.DEFINITION["version"],
                          "period": arguments["period"],
                          "sources": [{"id": r["source_id"], "kind": r["kind"]}
                                      for r in rows]}
            else:
                total_cents = sum(r["amount_cents"] * (
                    1 if r["kind"] == "paid_invoice" else -1) for r in rows)
                result = {"metric_id": self.DEFINITION["id"],
                          "definition_version": self.DEFINITION["version"],
                          "period": arguments["period"], "currency": "USD",
                          "value": str((Decimal(total_cents) / Decimal(100)).quantize(Decimal("0.01")))}
            return self._audit(tool, context, result)

    def _audit(self, tool, context, result):
        self.db.execute("INSERT INTO audit(at,subject,tenant,tool,outcome) VALUES (?,?,?,?,?)",
                        (time.time(), context.subject, context.tenant, tool,
                         result.get("error", "ok")))
        return result

    def audit_rows(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM audit ORDER BY id")]

    def close(self):
        self.db.close()
