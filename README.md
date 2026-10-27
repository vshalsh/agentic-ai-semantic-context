# Enterprise Agentic AI — Architecture, Articles & Executable Labs

**Four technical articles, four independent runnable code labs, automated tests, and an MIT license.**

Author: Vishal Sharma

## Read the articles

| # | Article | Article Markdown |
|---|---|---|
| 001 | AI Agents Are Getting Authority. Enterprise Architecture Hasn't Caught Up. | [Read](articles/001/article.md) |
| 002 | Building a Governed Agentic AI Runtime: MCP, Tool Calling, and Authorization | [Read](articles/002/article.md) |
| 003 | Your AI Agent Should Never Control Its Own Kill Switch | [Read](articles/003/article.md) |
| 004 | Your AI Agent Can Query the Data. Does It Understand What the Data Means? | [Read](articles/004/article.md) |

## Run the complete code labs

Each lab is self-contained, uses Python 3.10+ and the standard library, and has a dedicated README, command-line demo, and test suite.

| Lab | What it demonstrates | Documentation |
|---|---|---|
| [001 — Delegated Authority](examples/001-delegated-authority/) | SQLite-backed grants, amount limits, revocation, atomic approval, idempotency, audit | [README](examples/001-delegated-authority/README.md) |
| [002 — Governed Tools](examples/002-governed-tools/) | Tool schemas, trusted principal, tenant isolation, scope checks, approval limits, audit | [README](examples/002-governed-tools/README.md) |
| [003 — Independent Oversight](examples/003-independent-oversight/) | Task supervision, stop/revoke, task-bound capabilities, durable replay protection | [README](examples/003-independent-oversight/README.md) |
| [004 — Semantic Context](examples/004-semantic-context/) | Governed metric definitions, classification, tenant isolation, source lineage | [README](examples/004-semantic-context/README.md) |

Clone and run:

```bash
git clone https://github.com/vshalsh/agentic-ai-semantic-context.git
cd agentic-ai-semantic-context

python examples/001-delegated-authority/demo.py
python examples/002-governed-tools/demo.py
python examples/003-independent-oversight/demo.py
python examples/004-semantic-context/demo.py
```

Run the complete suite from the repository root:

```bash
python scripts/run_all_tests.py
```

GitHub Actions also runs the suite on pushes and pull requests.

## Repository structure

```text
.
├── articles/
│   ├── 001/article.md
│   ├── 002/article.md
│   ├── 003/article.md
│   └── 004/article.md
├── examples/
│   ├── 001-delegated-authority/  # service, CLI demo, tests, README
│   ├── 002-governed-tools/       # service, CLI demo, tests, README
│   ├── 003-independent-oversight/# supervisor, CLI demo, tests, README
│   └── 004-semantic-context/     # service, CLI demo, tests, README
├── scripts/run_all_tests.py
├── .github/workflows/python-tests.yml
└── LICENSE
```

## Important boundaries

These are **complete runnable educational labs**, not production deployments. They do not depend on external APIs, hosted LLMs, credentials, or paid services. The tool interfaces demonstrate MCP-inspired governance but are **not MCP protocol servers**. Integration with a real MCP SDK, OIDC, an external ERP, a policy engine, and production telemetry requires additional engineering.

Articles 001 and 002 are reconstructed manuscripts, rather than the original unavailable drafts. The code labs are maintained separately from the publication text. Older exploratory code remains in `articles/*` for reference; use `examples/*` for the documented, extended demonstrations.

## License

The repository's original code and documentation are provided under the [MIT License](LICENSE). Third-party source material and linked references retain their respective rights.
