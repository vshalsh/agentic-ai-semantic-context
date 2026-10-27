# Article 003 — Independent Agent Oversight

A standalone Python standard-library demonstration of an execution gateway that can reject actions independently of the model.

## Run

```bash
cd articles/003
python agent.py
python -m unittest -v test_demo.py
```

## Files

- `issuer.py`: task-scoped, expiring and revocable demo capabilities.
- `server.py`: execution boundary, task stop, idempotent success retries, and audit.
- `agent.py`: deterministic demonstration.
- `test_demo.py`: tests.
- `article.md`: accompanying editorial article.

**Security limitations:** In-memory only. The capability token is an opaque random identifier, not a signed credential. No distributed persistence, production authentication, transactional audit, or live LLM integration. Successful requests are idempotent within this process; failures are not cached. The implementation is an educational simplified companion, not the full implementation described in all passages of the article.
