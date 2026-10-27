# AI Agents Are Getting Authority. Enterprise Architecture Hasn't Caught Up.

*An enterprise architecture pattern for delegated authority, policy enforcement, and auditable AI actions.*

An AI agent that summarizes a document is useful. An agent that approves a payment, updates a vendor record, or changes access rights is a different class of system. It is exercising authority.

The central architectural question is not whether the model can use a tool. It is **whose authority the action represents, what boundaries apply, and how that authority can be revoked**.

## The authority gap

A traditional enterprise application typically knows the signed-in user, their role, and the authorization checks attached to each action. Agentic workflows complicate that picture. An agent may run asynchronously, call multiple tools, delegate tasks to subagents, and resume after the human who started it has gone offline.

A prompt saying "only approve small invoices" is not an authorization boundary. Neither is a tool description. The model's output is untrusted input to the business system.

## A practical execution model

Separate four concerns:

1. **Human sponsor:** The authenticated person or service requesting work.
2. **Delegation:** A short-lived, task-bound grant specifying allowed actions and limits.
3. **Policy decision:** A trusted service evaluating scope, tenant, amount, expiration, and revocation.
4. **Execution and evidence:** A deterministic tool gateway that checks policy before changing state and writes an audit record.

The agent may propose `approve_invoice(invoice_id)`. The gateway decides whether it may execute. The agent must never mint or enlarge its own grant.

## Reference flow

```text
Human sponsor -> authenticated task request
             -> delegation service (task, scope, expiry)
             -> agent planner
             -> tool gateway -> independent policy check
                             -> business API
                             -> append-only audit
```

The policy check should occur at the **point of execution**, not only when a workflow starts. A role change, revocation, or task cancellation must invalidate subsequent actions.

## A reproducible example

The companion Python demo in `demo.py` models a sponsor delegating authority to approve a single invoice under a monetary limit. It then demonstrates three cases: an authorized approval, an out-of-limit request, and an attempt to use a revoked grant.

Run:

```bash
python articles/001/demo.py
python -m unittest discover -s articles/001 -p 'test_*.py' -v
```

No cloud service or API key is required. All data is fictional.

## Design decisions worth making explicit

**Tenant binding:** The tenant is resolved from authenticated execution context, never accepted from model-generated arguments.

**Scope and object binding:** A grant names a task, action, and permitted business object. Generic "admin" permissions are inappropriate for narrowly delegated work.

**Revocation:** A grant can be valid when issued and invalid before the tool call. The gateway checks current grant state.

**Idempotency:** Replayed requests must not repeat consequential changes. A production system needs durable idempotency keys and transactional state changes.

**Evidence:** Audit records must capture sponsor, task, decision, resource, and result. Model-written summaries are not sufficient evidence.

## Where the demo stops

The example uses in-memory state and does not implement cryptographic tokens, real identity federation, distributed revocation, or durable audit storage. Those require production infrastructure and threat modeling.

The general principle remains: **the agent may request an action, but it must not be the final authority for that action**.

---

*This is a reconstructed standalone article based on the original topic, not a recovered verbatim manuscript.*
