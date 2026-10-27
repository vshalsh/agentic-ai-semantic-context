# Article 004 — Governed Semantic Context

A standalone, standard-library example of a governed semantic metric service. A model cannot change the trusted tenant, metric definition, or classification policy.

## Run

```bash
cd articles/004
python agent.py
python -m unittest -v test_demo.py
```

Expected October result: `1550.00 USD` from two paid invoices minus one issued credit. Draft invoices and another tenant's records are excluded.

## Files

- `server.py`: SQLite-backed semantic metric service, scoped tools, tenant binding, classification checks, and audit.
- `agent.py`: deterministic tool orchestration example.
- `test_demo.py`: tests for metrics, lineage, scope, classification, and argument spoofing.
- `article.md`: accompanying editorial article.

**Important:** This implementation is an educational MCP-style service interface, **not a complete MCP stdio/HTTP protocol server**. The sample uses trusted context passed by application code, not a real identity provider. It does not connect to a live model or production data. It is a simplified executable companion rather than an exact copy of the full downloadable project.
