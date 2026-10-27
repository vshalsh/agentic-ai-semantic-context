"""Article 002: MCP-style governed invoice tool gateway (not full MCP wire protocol)."""
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class Context:
    principal: str
    tenant: str
    scopes: frozenset
    approval_limit: int

class ToolGateway:
    ALLOWED = {"read_invoice", "approve_invoice"}
    def __init__(self):
        self.invoices = {
            ("acme", "A-100"): {"amount": 150, "status": "pending", "description": "Office supplies"},
            ("other", "B-900"): {"amount": 900, "status": "pending", "description": "Other tenant"},
        }
        self.audit = []

    def call(self, name, arguments, context):
        if name not in self.ALLOWED:
            return self._result(name, context, "unknown_tool")
        if set(arguments) != {"invoice_id"} or not isinstance(arguments.get("invoice_id"), str):
            return self._result(name, context, "invalid_arguments")
        required = "invoice.read" if name == "read_invoice" else "invoice.approve"
        if required not in context.scopes:
            return self._result(name, context, "missing_scope")
        invoice = self.invoices.get((context.tenant, arguments["invoice_id"]))
        if invoice is None:
            return self._result(name, context, "not_found")
        if name == "approve_invoice":
            if invoice["amount"] > context.approval_limit:
                return self._result(name, context, "approval_limit")
            if invoice["status"] != "pending":
                return self._result(name, context, "already_processed")
            invoice["status"] = "approved"
        return self._result(name, context, "ok", {"invoice_id": arguments["invoice_id"], **invoice})

    def _result(self, tool, context, status, data=None):
        self.audit.append({"principal": context.principal, "tenant": context.tenant, "tool": tool, "status": status})
        return {"status": status, "data": data}

def demo():
    gateway = ToolGateway()
    admin = Context("alice", "acme", frozenset({"invoice.read", "invoice.approve"}), 200)
    reader = Context("bob", "acme", frozenset({"invoice.read"}), 0)
    print("READ", json.dumps(gateway.call("read_invoice", {"invoice_id": "A-100"}, admin)))
    print("DENIED", json.dumps(gateway.call("approve_invoice", {"invoice_id": "A-100"}, reader)))
    print("CROSS_TENANT", json.dumps(gateway.call("read_invoice", {"invoice_id": "B-900"}, admin)))
    print("APPROVE", json.dumps(gateway.call("approve_invoice", {"invoice_id": "A-100"}, admin)))

if __name__ == "__main__":
    demo()
