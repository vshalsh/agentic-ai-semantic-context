"""Article 001: delegated authority at the execution boundary (stdlib only)."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json

@dataclass
class Grant:
    sponsor: str
    tenant: str
    task: str
    action: str
    resource: str
    max_amount: int
    expires_at: datetime
    revoked: bool = False

class Gateway:
    def __init__(self):
        self.invoices = {("acme", "INV-1"): {"amount": 120, "status": "pending"}}
        self.audit = []

    def approve(self, grant, tenant, task, invoice_id):
        record = self.invoices.get((tenant, invoice_id))
        reason = None
        if grant.revoked or datetime.now(timezone.utc) >= grant.expires_at:
            reason = "grant_inactive"
        elif (grant.tenant, grant.task, grant.action, grant.resource) != (tenant, task, "invoice.approve", invoice_id):
            reason = "delegation_mismatch"
        elif record is None:
            reason = "not_found"
        elif record["amount"] > grant.max_amount:
            reason = "amount_limit"
        elif record["status"] != "pending":
            reason = "already_processed"
        if reason is None:
            record["status"] = "approved"
        outcome = {"allowed": reason is None, "reason": reason or "approved", "invoice_id": invoice_id}
        self.audit.append({"sponsor": grant.sponsor, "task": task, **outcome})
        return outcome

def demo():
    gateway = Gateway()
    grant = Grant("alice", "acme", "task-1", "invoice.approve", "INV-1", 200,
                  datetime.now(timezone.utc) + timedelta(minutes=5))
    print("APPROVE", json.dumps(gateway.approve(grant, "acme", "task-1", "INV-1")))
    grant.revoked = True
    print("REVOKED", json.dumps(gateway.approve(grant, "acme", "task-1", "INV-1")))
    print("AUDIT", json.dumps(gateway.audit))

if __name__ == "__main__":
    demo()
