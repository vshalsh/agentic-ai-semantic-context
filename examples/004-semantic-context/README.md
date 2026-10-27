# 004 — Governed Semantic Context: Full Runnable Demo

**Architecture:** agent → governed tool interface → trusted user/tenant context → metric registry → classification policy → tenant-filtered SQLite facts → deterministic calculation → lineage and audit.

The agent may request a metric and period. It cannot redefine the metric, select another tenant, bypass classification, or fabricate source lineage. Monetary arithmetic uses integer cents, with `Decimal` only for formatting.

## Run

```bash
cd examples/004-semantic-context
python demo.py
python demo.py --tenant acme --period 2026-11
python -m unittest discover -p 'test_*.py' -v
```

Python 3.10+, no external dependencies.

Expected October result: **USD 1,550.00**. Sources: AC-I1 + AC-I2 − AC-C1. Draft invoices are excluded. November's restricted record is denied without `data.restricted`. Tenant spoofing in tool arguments is rejected.

## Files

- `semantic.py`: governed metric definition, SQLite facts, tenant isolation, classification, lineage, audit.
- `demo.py`: complete CLI walkthrough.
- `test_semantic.py`: eight tests.

## Extension points

Replace `DEFINITION` with a versioned registry; add a trusted OIDC-derived `Context`; connect to your warehouse through an authorized query layer; map sources to a data catalog; expose the gateway through a conformant MCP SDK; add data-quality contracts and change approval.

This example is a **governed MCP-style tool interface, not a complete MCP wire-protocol server**. It does not invoke a model or a production database.
