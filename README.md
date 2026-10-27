# Enterprise Agentic AI — Architecture & Working Examples

A growing collection of independent, technical articles and companion implementations on enterprise Agentic AI architecture.

**Author:** Vishal Sharma

Each article is designed to stand alone. Source code is educational and is not production-ready without appropriate security and operational controls.

## Articles

| Article | Topic | Implementation |
|---|---|---|
| 001 | Agent identity, delegated authority, and governance | Editorial article; companion pending |
| 002 | Governed MCP runtime: orchestrator, tool calling, scoped authorization, audit | Python example; upload pending |
| 003 | Independent agent oversight, signed task permissions, durable execution | Python example; upload pending |
| 004 | Governed semantic context: metric definitions, tenant isolation, lineage | Python example; upload pending |

## Repository layout

```text
articles/
  001/
  002/
  003/
  004/
```

Each numbered directory is intended to contain its article and, where available, executable code, tests, and a local README.

## Principles

- Agent reasoning does not replace enterprise authorization.
- MCP connectivity does not automatically establish access rights.
- Business definitions and tenant boundaries belong in trusted services.
- Audit evidence must be independent of model-generated explanations.
- Examples should include runnable tests and explicit limitations.

## Publishing

Articles are reviewed and published separately on Medium. No Medium publication is performed by this repository.

## Security

Do not commit API keys, credentials, production data, or environment files. The demos are intentionally simplified and should not be deployed as production services without review.

## License

No open-source license has been selected yet. All rights reserved unless a license is added.
