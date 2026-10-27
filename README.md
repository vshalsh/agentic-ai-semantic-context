# Enterprise Agentic AI — Architecture and Working Examples

Four independent technical articles with executable Python demonstrations and automated tests.

**Author:** Vishal Sharma

| Article | Subject | Links |
|---|---|---|
| 001 | Delegated authority and revocation | [Article](articles/001/article.md) · [Code](articles/001/demo.py) · [Tests](articles/001/test_demo.py) |
| 002 | Governed MCP-style tool calling and authorization | [Article](articles/002/article.md) · [Code](articles/002/demo.py) · [Tests](articles/002/test_demo.py) |
| 003 | Independent oversight and agent kill switches | [Article](articles/003/article.md) · [Code](articles/003/agent.py) · [Tests](articles/003/test_demo.py) |
| 004 | Semantic context, tenant isolation, metric lineage | [Article](articles/004/article.md) · [Code](articles/004/agent.py) · [Tests](articles/004/test_demo.py) |

## Quick start

Python 3.10+ is recommended. All committed demos use the standard library.

```bash
python articles/001/demo.py
python articles/002/demo.py
python articles/003/agent.py
python articles/004/agent.py
```

Run tests from within each article directory:

```bash
cd articles/001 && python -m unittest -v test_demo.py
cd ../002 && python -m unittest -v test_demo.py
cd ../003 && python -m unittest -v test_demo.py
cd ../004 && python -m unittest -v test_demo.py
```

GitHub Actions runs the same test suites on pushes and pull requests.

## Scope and provenance

Articles 001 and 002 are **reconstructed manuscripts**, not recovered verbatim originals. Articles 003 and 004 preserve the available Markdown drafts. The committed 003/004 Python implementations are **simplified self-contained companions** and are not byte-identical to the previously generated downloadable ZIP.

The tool examples illustrate MCP-style boundaries, but **are not full MCP protocol servers**. They intentionally do not require cloud credentials, paid APIs, or external databases. Do not interpret them as production-ready enterprise identity, security, audit, or distributed transaction systems.

## Security and licensing

Never commit API keys, production records, or credentials. No open-source license has been selected; all rights reserved until one is added.
