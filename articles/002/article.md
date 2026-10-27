# Building a Governed Agentic AI Runtime: MCP, Tool Calling, and Authorization

*An executable pattern for keeping tool discovery separate from permission to execute.*

Model Context Protocol (MCP) makes tools easier for AI systems to discover and call. That is an integration improvement, not an automatic security guarantee. A tool schema tells an agent **how** to request an operation. It does not establish **whether** the agent may perform it.

For enterprise use, a tool call should pass through a deterministic execution boundary that validates arguments, binds trusted identity, checks authorization, enforces business rules, and records the outcome.

## The architecture

```text
User -> Agent planner -> tool request
                      -> MCP-compatible tool adapter
                      -> argument validation
                      -> trusted execution context
                      -> policy enforcement
                      -> business service
                      -> audit record
                      -> tool result -> Agent explanation
```

The model chooses a tool. The gateway decides whether the requested operation is authorized. The source system remains responsible for enforcing its own permissions.

## Example: invoice approvals

Consider an invoice workflow with two tools:

- `read_invoice(invoice_id)`: return an invoice from the authenticated tenant.
- `approve_invoice(invoice_id)`: approve only when the trusted principal has `invoice.approve`, the invoice is eligible, and the approval amount is within their limit.

The model must not be allowed to provide `tenant_id`, `role`, or `approval_limit` as tool arguments. These belong to authenticated context.

The accompanying `demo.py` implements the trusted gateway and demonstrates successful approval, missing-scope denial, and cross-tenant isolation. It uses a deliberately small MCP-style tool surface; **it is not a full MCP protocol server**.

## Run locally

```bash
python articles/002/demo.py
python -m unittest discover -s articles/002 -p 'test_*.py' -v
```

Python standard library only; no model API or network connection is required.

## Why a policy check belongs outside the model

Models can misinterpret instructions, receive adversarial tool output, or call the wrong tool. A gateway that evaluates structured policy inputs can reject the operation regardless of why it was proposed.

Authorization should consider the identity of the sponsor, the delegated task, the tenant, the resource, the action, and the time of execution. Where approval is consequential, human confirmation or a separate approval service may be required.

## Failure modes

**Prompt-injected authority:** An invoice description says "ignore limits." The gateway ignores it because descriptions are data, not policy.

**Cross-tenant identifiers:** A guessed invoice ID from another tenant returns no usable business record.

**Over-broad scopes:** `invoice.read` does not imply `invoice.approve`.

**Stale approval rights:** A production gateway should re-evaluate role changes and revoked grants before execution.

**Partial side effects:** Real integrations require durable idempotency, transaction boundaries, retry classification, and reconciliation.

## Production considerations

A production MCP implementation also needs authenticated transport, protocol-conformant messaging, secure secret handling, tool registry governance, structured tracing, policy service availability planning, and tamper-evident audit retention.

The sample is intentionally small enough to inspect. It demonstrates where the trust boundary belongs, rather than pretending that an in-memory example is enterprise infrastructure.

The key distinction: **tool connectivity enables action; authorization legitimizes it**.

---

*This is a reconstructed standalone article based on the original topic, not a recovered verbatim manuscript.*
