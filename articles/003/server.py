"""Independent execution boundary with revocation, idempotency and audit."""
from issuer import Issuer

class Runtime:
    def __init__(self, issuer=None):
        self.issuer = issuer or Issuer()
        self.state = {("acme", "INV-1"): "pending"}
        self.processed = {}
        self.stopped_tasks = set()
        self.audit = []

    def stop(self, task_id):
        self.stopped_tasks.add(task_id)

    def execute(self, *, token, task_id, tenant, action, resource, request_id):
        key = (task_id, request_id)
        if key in self.processed:
            return self.processed[key]
        if task_id in self.stopped_tasks:
            result = {"ok": False, "reason": "task_stopped"}
        elif not self.issuer.validate(token, task_id, tenant, action, resource):
            result = {"ok": False, "reason": "capability_denied"}
        elif action != "invoice.approve" or (tenant, resource) not in self.state:
            result = {"ok": False, "reason": "not_found"}
        elif self.state[(tenant, resource)] != "pending":
            result = {"ok": False, "reason": "already_processed"}
        else:
            self.state[(tenant, resource)] = "approved"
            result = {"ok": True, "reason": "approved"}
        self.audit.append({"task_id": task_id, "request_id": request_id,
                           "resource": resource, **result})
        if result["ok"]:
            self.processed[key] = result
        return result
