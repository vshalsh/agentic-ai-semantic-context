"""Run: python demo.py --db /tmp/agent-authority.sqlite"""
import argparse
import json
from authority import AuthorityService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=":memory:", help="SQLite path; default in-memory")
    args = parser.parse_args()
    service = AuthorityService(args.db)
    service.seed_invoice("acme", "INV-101", 15000)
    service.seed_invoice("acme", "INV-102", 90000)
    token = service.delegate(sponsor="alice", tenant="acme", task_id="task-101",
                             resource="INV-101", limit_cents=20000)
    operation = dict(token=token, tenant="acme", task_id="task-101", resource="INV-101")
    print("AUTHORIZED", json.dumps(vars(service.approve(**operation, request_id="op-1"))))
    print("RETRY", json.dumps(vars(service.approve(**operation, request_id="op-1"))))
    print("CONFLICT", json.dumps(vars(service.approve(**{**operation, "resource": "INV-102"},
                                                      request_id="op-1"))))
    service.revoke(token)
    print("REVOKED", json.dumps(vars(service.approve(**operation, request_id="op-2"))))
    print("AUDIT", json.dumps(service.audit(), indent=2))
    service.close()


if __name__ == "__main__":
    main()
