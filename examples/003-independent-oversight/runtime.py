"""Independent agent execution supervisor: durable stop, revoke, retry and audit.

The supervisor, not the agent, owns task state and capability issuance.
"""
from __future__ import annotations
import json
import secrets
import sqlite3
import threading
import time


class Supervisor:
    def __init__(self, db_path=":memory:"):
        self.db = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks(
                id TEXT PRIMARY KEY, tenant TEXT NOT NULL,
                sponsor TEXT NOT NULL, stopped INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS capabilities(
                token TEXT PRIMARY KEY, task_id TEXT NOT NULL, tenant TEXT NOT NULL,
                action TEXT NOT NULL, resource TEXT NOT NULL,
                expires_at REAL NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS invoices(
                tenant TEXT NOT NULL, id TEXT NOT NULL, status TEXT NOT NULL,
                PRIMARY KEY(tenant,id));
            CREATE TABLE IF NOT EXISTS executions(
                task_id TEXT NOT NULL, request_id TEXT NOT NULL,
                fingerprint TEXT NOT NULL, result_json TEXT NOT NULL,
                PRIMARY KEY(task_id,request_id));
            CREATE TABLE IF NOT EXISTS audit(
                id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                task_id TEXT NOT NULL, request_id TEXT NOT NULL,
                action TEXT NOT NULL, resource TEXT NOT NULL, reason TEXT NOT NULL);
        """)

    def register_task(self, task_id, tenant, sponsor):
        with self.lock:
            self.db.execute("INSERT INTO tasks(id,tenant,sponsor) VALUES (?,?,?)",
                            (task_id, tenant, sponsor))

    def seed_invoice(self, tenant, invoice_id):
        self.db.execute("INSERT OR IGNORE INTO invoices VALUES (?,?,'pending')",
                        (tenant, invoice_id))

    def issue(self, task_id, action, resource, ttl_seconds=300):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        with self.lock:
            task = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not task or task["stopped"]:
                raise PermissionError("task is absent or stopped")
            token = secrets.token_urlsafe(32)
            self.db.execute("INSERT INTO capabilities VALUES (?,?,?,?,?,?,0)",
                            (token, task_id, task["tenant"], action, resource,
                             time.time() + ttl_seconds))
            return token

    def stop(self, task_id):
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                self.db.execute("UPDATE tasks SET stopped=1 WHERE id=?", (task_id,))
                self.db.execute("UPDATE capabilities SET revoked=1 WHERE task_id=?", (task_id,))
                self.db.execute("COMMIT")
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def revoke(self, token):
        with self.lock:
            self.db.execute("UPDATE capabilities SET revoked=1 WHERE token=?", (token,))

    def execute(self, *, token, task_id, tenant, action, resource, request_id):
        if not all((token, task_id, tenant, action, resource, request_id)):
            raise ValueError("missing required field")
        fingerprint = json.dumps([tenant, action, resource], separators=(",", ":"))
        with self.lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                prior = self.db.execute("SELECT * FROM executions WHERE task_id=? AND request_id=?",
                                        (task_id, request_id)).fetchone()
                if prior:
                    result = (json.loads(prior["result_json"]) if prior["fingerprint"] == fingerprint
                              else {"ok": False, "reason": "idempotency_conflict"})
                    self.db.execute("COMMIT")
                    return result

                task = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
                cap = self.db.execute("SELECT * FROM capabilities WHERE token=?", (token,)).fetchone()
                invoice = self.db.execute("SELECT * FROM invoices WHERE tenant=? AND id=?",
                                          (tenant, resource)).fetchone()
                if not task or task["stopped"]:
                    reason = "task_stopped"
                elif task["tenant"] != tenant:
                    reason = "tenant_mismatch"
                elif not cap or cap["revoked"] or cap["expires_at"] <= time.time():
                    reason = "capability_inactive"
                elif (cap["task_id"], cap["tenant"], cap["action"], cap["resource"]) != (
                    task_id, tenant, action, resource):
                    reason = "capability_mismatch"
                elif action != "invoice.approve" or not invoice:
                    reason = "unsupported_operation"
                elif invoice["status"] != "pending":
                    reason = "already_processed"
                else:
                    reason = "approved"
                    self.db.execute("UPDATE invoices SET status='approved' WHERE tenant=? AND id=?",
                                    (tenant, resource))
                result = {"ok": reason == "approved", "reason": reason}
                self.db.execute("INSERT INTO executions VALUES (?,?,?,?)",
                                (task_id, request_id, fingerprint, json.dumps(result)))
                self.db.execute("INSERT INTO audit(at,task_id,request_id,action,resource,reason) VALUES (?,?,?,?,?,?)",
                                (time.time(), task_id, request_id, action, resource, reason))
                self.db.execute("COMMIT")
                return result
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def audit(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM audit ORDER BY id")]

    def close(self):
        self.db.close()
