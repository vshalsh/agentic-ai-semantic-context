"""Durable, task-scoped delegated authorization; Python stdlib only.

Security boundary: the trusted caller supplies sponsor/tenant context; the agent
can propose a resource/action but cannot mint, modify, or revoke capabilities.
"""
from __future__ import annotations

import json
import secrets
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str
    resource: str
    task_id: str


class AuthorityService:
    """SQLite-backed capability grants, approvals, and durable audit.

    The SQLite transaction serializes the authorization decision and mutation.
    For production, place this service behind authenticated transport and use a
    managed relational database with appropriate isolation and observability.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self.db.executescript("""
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS invoices(
                tenant TEXT NOT NULL, id TEXT NOT NULL,
                amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0),
                status TEXT NOT NULL CHECK(status IN ('pending','approved')),
                PRIMARY KEY(tenant,id)
            );
            CREATE TABLE IF NOT EXISTS grants(
                token TEXT PRIMARY KEY, sponsor TEXT NOT NULL, tenant TEXT NOT NULL,
                task_id TEXT NOT NULL, action TEXT NOT NULL, resource TEXT NOT NULL,
                limit_cents INTEGER NOT NULL, expires_at REAL NOT NULL,
                revoked INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS decisions(
                id INTEGER PRIMARY KEY AUTOINCREMENT, at REAL NOT NULL,
                sponsor TEXT, tenant TEXT NOT NULL, task_id TEXT NOT NULL,
                resource TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS operations(
                tenant TEXT NOT NULL, task_id TEXT NOT NULL, request_id TEXT NOT NULL,
                resource TEXT NOT NULL, allowed INTEGER NOT NULL, reason TEXT NOT NULL,
                PRIMARY KEY(tenant,task_id,request_id)
            );
        """)

    def seed_invoice(self, tenant: str, invoice_id: str, amount_cents: int):
        with self._lock:
            self.db.execute("INSERT OR IGNORE INTO invoices VALUES (?,?,?,'pending')",
                            (tenant, invoice_id, amount_cents))

    def delegate(self, *, sponsor: str, tenant: str, task_id: str,
                 resource: str, limit_cents: int, ttl_seconds: int = 300) -> str:
        if not all((sponsor, tenant, task_id, resource)) or limit_cents < 0 or ttl_seconds <= 0:
            raise ValueError("invalid delegation")
        token = secrets.token_urlsafe(32)
        with self._lock:
            self.db.execute(
                "INSERT INTO grants VALUES (?,?,?,?,?,?,?,?,0)",
                (token, sponsor, tenant, task_id, "invoice.approve", resource,
                 limit_cents, time.time() + ttl_seconds))
        return token

    def revoke(self, token: str) -> bool:
        with self._lock:
            cursor = self.db.execute("UPDATE grants SET revoked=1 WHERE token=?", (token,))
            return cursor.rowcount == 1

    def approve(self, *, token: str, tenant: str, task_id: str,
                resource: str, request_id: str) -> Decision:
        if not all((tenant, task_id, resource, request_id)):
            raise ValueError("missing required argument")
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try:
                prior = self.db.execute(
                    "SELECT * FROM operations WHERE tenant=? AND task_id=? AND request_id=?",
                    (tenant, task_id, request_id)).fetchone()
                if prior:
                    if prior["resource"] != resource:
                        result = Decision(False, "idempotency_conflict", resource, task_id)
                    else:
                        result = Decision(bool(prior["allowed"]), prior["reason"], resource, task_id)
                    self.db.execute("COMMIT")
                    return result

                grant = self.db.execute("SELECT * FROM grants WHERE token=?", (token,)).fetchone()
                invoice = self.db.execute(
                    "SELECT * FROM invoices WHERE tenant=? AND id=?", (tenant, resource)).fetchone()
                sponsor = grant["sponsor"] if grant else None
                if not grant or grant["revoked"] or grant["expires_at"] <= time.time():
                    reason = "grant_inactive"
                elif (grant["tenant"], grant["task_id"], grant["resource"], grant["action"]) != (
                    tenant, task_id, resource, "invoice.approve"):
                    reason = "delegation_mismatch"
                elif invoice is None:
                    reason = "not_found"
                elif invoice["amount_cents"] > grant["limit_cents"]:
                    reason = "amount_limit"
                elif invoice["status"] != "pending":
                    reason = "already_processed"
                else:
                    reason = "approved"
                    self.db.execute("UPDATE invoices SET status='approved' WHERE tenant=? AND id=?",
                                    (tenant, resource))
                allowed = reason == "approved"
                self.db.execute("INSERT INTO decisions(at,sponsor,tenant,task_id,resource,allowed,reason) VALUES (?,?,?,?,?,?,?)",
                                (time.time(), sponsor, tenant, task_id, resource, int(allowed), reason))
                self.db.execute("INSERT INTO operations VALUES (?,?,?,?,?,?)",
                                (tenant, task_id, request_id, resource, int(allowed), reason))
                self.db.execute("COMMIT")
                return Decision(allowed, reason, resource, task_id)
            except Exception:
                self.db.execute("ROLLBACK")
                raise

    def audit(self):
        return [dict(row) for row in self.db.execute("SELECT * FROM decisions ORDER BY id")]

    def invoice_status(self, tenant: str, resource: str) -> Optional[str]:
        row = self.db.execute("SELECT status FROM invoices WHERE tenant=? AND id=?",
                              (tenant, resource)).fetchone()
        return row["status"] if row else None

    def close(self):
        self.db.close()
