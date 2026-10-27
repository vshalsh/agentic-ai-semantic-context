# 003 — Independent Agent Oversight: Full Runnable Demo

**Architecture:** human sponsor → supervisor-controlled task → task-scoped capability → independent execution gateway → transactional business mutation and audit.

An agent never receives permission to call `Supervisor.issue()`, `Supervisor.revoke()`, or `Supervisor.stop()` in a real deployment. These methods represent privileged control-plane operations.

## Run

```bash
cd examples/003-independent-oversight
python demo.py
python -m unittest discover -p 'test_*.py' -v
```

Python 3.10+, standard library only.

Expected: first approval succeeds, exact retry returns the stored result, unauthorized resource is rejected, operator stop prevents subsequent operations, and the audit captures each new decision.

## Files

- `runtime.py`: SQLite-backed supervisor, tasks, capabilities, revocation, stop, idempotency, and audit.
- `demo.py`: end-to-end execution and operator stop.
- `test_runtime.py`: seven tests.

## Why the stop works

The supervisor checks current task state **inside the same database transaction as the business mutation**. The agent's own reasoning process is not trusted to honor a cancellation request. Stopping a task also revokes its existing capabilities.

Idempotent replays return the original result, even after a stop; they do not execute a new operation. This is intentional for reconciliation.

## Production boundary

The demo is a single-process implementation. Deploy the supervisor as an independently authorized service, use authenticated transport and a database appropriate for your concurrency needs, and add durable queues, outbox events, rate limits, secure token handling, and tamper-evident audit exports. A task stop cannot undo an external side effect that already completed.
