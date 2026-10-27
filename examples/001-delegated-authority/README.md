# 001 — Delegated Authority: Full Runnable Demo

**Architecture:** human sponsor → trusted delegation service → untrusted agent request → transactionally enforced policy → invoice state → durable audit.

This example uses SQLite persistence and a single transaction for authorization, mutation, idempotency, and audit. Grants are random opaque tokens, bound to a tenant, task, invoice, action, monetary limit, and expiration. Revocation is checked on every **new** operation.

## Run

Python 3.10+, no dependencies:

```bash
cd examples/001-delegated-authority
python demo.py
python -m unittest discover -p 'test_*.py' -v
python demo.py --db authority.sqlite
```

Expected: `AUTHORIZED` true, `RETRY` true without a second mutation, `CONFLICT` denied, `REVOKED` denied, and audit rows.

## File map

- `authority.py`: durable service, SQLite schema, delegation, revocation, policy, audit.
- `demo.py`: complete command-line walkthrough.
- `test_authority.py`: policy, tenant isolation, idempotency, persistence tests.

## Trust boundaries

The caller of `delegate()` is assumed to be an authenticated, trusted service. The agent is **never** given authority to call that method. In a deployed system, enforce this with separate services and authenticated transport. A cached successful idempotency replay returns the original result even after revocation; it **does not** execute a new side effect.

## Not included

OIDC identity verification, signed delegation credentials, distributed revocation, multi-region locking, external ERP integration, tamper-evident audit exports, or real payment processing. Those are deployment-specific concerns, not claims of this example.
