"""Article 003: a model-independent example of an independently stoppable agent."""
import json
from issuer import Issuer
from server import Runtime

def run_demo():
    issuer = Issuer()
    runtime = Runtime(issuer)
    token = issuer.issue("task-1", "acme", "invoice.approve", "INV-1")
    request = dict(token=token, task_id="task-1", tenant="acme",
                   action="invoice.approve", resource="INV-1", request_id="op-1")
    print("APPROVED", json.dumps(runtime.execute(**request)))
    print("IDEMPOTENT_RETRY", json.dumps(runtime.execute(**request)))
    runtime.stop("task-1")
    request["request_id"] = "op-2"
    print("STOPPED", json.dumps(runtime.execute(**request)))
    issuer.revoke(token)
    print("AUDIT", json.dumps(runtime.audit))
    return runtime

if __name__ == "__main__":
    run_demo()
