# 002 — Governed Tool Calling: Full Runnable Demo

**Architecture:** tool discovery → model-proposed tool arguments → schema validation → trusted identity context → scope and tenant checks → invoice service → transactional audit.

The agent may see tool names and arguments, but cannot provide a tenant, role, or monetary limit. Those are supplied by the authenticated application as a `Principal`. Read and approve are separate scopes. Consequential approvals use durable idempotency records.

## Run

```bash
cd examples/002-governed-tools
python demo.py
python -m unittest discover -p 'test_*.py' -v
```

No dependencies outside Python 3.10+. Output includes tool discovery, successful read, missing-scope rejection, tenant spoof rejection, cross-tenant isolation, approval, retry, and audit.

## Files

- `gateway.py`: tool schema, authorization, SQLite invoices, approval idempotency, audit.
- `demo.py`: complete deterministic demonstration.
- `test_gateway.py`: seven tests.

## MCP boundary

This is a **governed tool runtime with MCP-style tool discovery**, not an MCP wire-protocol implementation. To expose these tools over a real MCP server, integrate an MCP SDK and transport authentication, then delegate every tool execution to `GovernedGateway.call()`. Do not allow a model to construct `Principal`.

## Production hardening

Add identity federation, a central policy decision point, human approval, key management, distributed concurrency control, source-system authorization, sensitive-data filtering, and tamper-evident audit retention.
