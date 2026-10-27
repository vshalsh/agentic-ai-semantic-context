"""Governed tool gateway with SQLite data, trusted identity and durable audit."""
from __future__ import annotations
import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class Principal:
    subject: str
    tenant: str
    scopes: FrozenSet[str]
    approval_limit_cents: int


class GovernedGateway:
    """Tool schema is not authorization; this gateway owns the policy boundary."""

    TOOL_SCHEMAS = {
        "read_invoice": {"invoice_id": str},
        "approve_invoice": {"invoice_id": str, "request_id": str},
    }

    def __init__(self, db_path=":memory:"):
        self.db = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS invoices(
                tenant TEXT NOT NULL, id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL, status TEXT NOT NULL,
                description TEXT NOT NULL, PRIMARY KEY(tenant,id));
            CREATE TABLE IF NOT EXISTS operations(
                tenant TEXT NOT NULL, subject TEXT NOT NULL, request_id TEXT NOT NULL,
                invoice_id TEXT NOT NULL, result_json TEXT NOT NULL,
                PRIMARY KEY(tenant,subject,request_id));
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                subject TEXT NOT NULL, tenant TEXT NOT NULL, tool TEXT NOT NULL,
                status TEXT NOT NULL);
        """)

    def seed(self):
        self.db.executemany("INSERT OR IGNORE INTO invoices VALUES (?,?,?,?,?)", [
            ("acme", "A-100", 15000, "pending", "Office supplies"),
            ("acme", "A-200", 45000, "pending", "Workstation"),
            ("other", "B-900", 90000, "pending", "Other tenant"),
        ])

    def tools(self):
        """Expose only nonprivileged JSON-like schemas to an agent."""
        return [{"name": name, "arguments": list(schema)}
                for name, schema in self.TOOL_SCHEMAS.items()]

    def call(self, name: str, arguments: dict, principal: Principal) -> dict:
        with self.lock:
            if name not in self.TOOL_SCHEMAS:
                return self._audit(name, principal, {"status": "unknown_tool"})
            schema = self.TOOL_SCHEMAS[name]
            if not isinstance(arguments, dict) or set(arguments) != set(schema) or any(
                    not isinstance(arguments[k], typ) or not arguments[k]
                    for k, typ in schema.items()):
                return self._audit(name, principal, {"status": "invalid_arguments"})
            scope = "invoice.read" if name == "read_invoice" else "invoice.approve"
            if scope not in principal.scopes:
                return self._audit(name, principal, {"status": "missing_scope"})
            if name == "read_invoice":
                row = self.db.execute("SELECT * FROM invoices WHERE tenant=? AND id=?",
                                      (principal.tenant, arguments["invoice_id"])).fetchone()
                return self._audit(name, principal,
                    {"status": "ok", "invoice": dict(row)} if row else {"status": "not_found"})
            return self._approve(arguments, principal)

    def _approve(self, args, principal):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            prior = self.db.execute(
                "SELECT * FROM operations WHERE tenant=? AND subject=? AND request_id=?",
                (principal.tenant, principal.subject, args["request_id"])).fetchone()
            if prior:
                result = (json.loads(prior["result_json"]) if prior["invoice_id"] == args["invoice_id"]
                          else {"status": "idempotency_conflict"})
            else:
                row = self.db.execute("SELECT * FROM invoices WHERE tenant=? AND id=?",
                                      (principal.tenant, args["invoice_id"])).fetchone()
                if row is None:
                    result = {"status": "not_found"}
                elif row["amount_cents"] > principal.approval_limit_cents:
                    result = {"status": "approval_limit"}
                elif row["status"] != "pending":
                    result = {"status": "already_processed"}
                else:
                    self.db.execute("UPDATE invoices SET status='approved' WHERE tenant=? AND id=?",
                                    (principal.tenant, args["invoice_id"]))
                    result = {"status": "ok", "invoice_id": args["invoice_id"]}
                self.db.execute("INSERT INTO operations VALUES (?,?,?,?,?)",
                                (principal.tenant, principal.subject, args["request_id"],
                                 args["invoice_id"], json.dumps(result)))
            self.db.execute("INSERT INTO audit(at,subject,tenant,tool,status) VALUES (?,?,?,?,?)",
                            (time.time(), principal.subject, principal.tenant,
                             "approve_invoice", result["status"]))
            self.db.execute("COMMIT")
            return result
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    def _audit(self, tool, principal, result):
        self.db.execute("INSERT INTO audit(at,subject,tenant,tool,status) VALUES (?,?,?,?,?)",
                        (time.time(), principal.subject, principal.tenant, tool, result["status"]))
        return result

    def audit_rows(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM audit ORDER BY id")]

    def close(self):
        self.db.close()
