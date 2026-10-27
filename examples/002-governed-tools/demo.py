"""Run: python demo.py"""
import json
from gateway import GovernedGateway, Principal


def main():
    gateway = GovernedGateway()
    gateway.seed()
    approver = Principal("alice", "acme", frozenset({"invoice.read", "invoice.approve"}), 20000)
    reader = Principal("bob", "acme", frozenset({"invoice.read"}), 0)
    cases = [
        ("DISCOVER", gateway.tools()),
        ("READ", gateway.call("read_invoice", {"invoice_id": "A-100"}, approver)),
        ("DENY_SCOPE", gateway.call("approve_invoice",
                                    {"invoice_id": "A-100", "request_id": "op1"}, reader)),
        ("DENY_TENANT_SPOOF", gateway.call("read_invoice",
                                          {"invoice_id": "A-100", "tenant": "other"}, approver)),
        ("ISOLATE_TENANT", gateway.call("read_invoice", {"invoice_id": "B-900"}, approver)),
        ("APPROVE", gateway.call("approve_invoice",
                                 {"invoice_id": "A-100", "request_id": "op2"}, approver)),
        ("RETRY", gateway.call("approve_invoice",
                               {"invoice_id": "A-100", "request_id": "op2"}, approver)),
    ]
    for label, result in cases:
        print(label, json.dumps(result))
    print("AUDIT", json.dumps(gateway.audit_rows(), indent=2))
    gateway.close()


if __name__ == "__main__":
    main()
