"""Run: python demo.py"""
import json
from runtime import Supervisor


def main():
    supervisor = Supervisor()
    supervisor.register_task("task-1", "acme", "alice")
    supervisor.seed_invoice("acme", "INV-1")
    supervisor.seed_invoice("acme", "INV-2")
    token = supervisor.issue("task-1", "invoice.approve", "INV-1")
    args = dict(token=token, task_id="task-1", tenant="acme",
                action="invoice.approve", resource="INV-1")
    print("FIRST", json.dumps(supervisor.execute(**args, request_id="op-1")))
    print("RETRY", json.dumps(supervisor.execute(**args, request_id="op-1")))
    print("MISMATCH", json.dumps(supervisor.execute(
        **{**args, "resource": "INV-2"}, request_id="op-2")))
    supervisor.stop("task-1")
    print("AFTER_STOP", json.dumps(supervisor.execute(**args, request_id="op-3")))
    print("AUDIT", json.dumps(supervisor.audit(), indent=2))
    supervisor.close()


if __name__ == "__main__":
    main()
