# Your AI Agent Can Query the Data. Does It Understand What the Data Means?

*Building a governed semantic context layer with MCP, tenant-aware retrieval, source lineage, and an executable Python example.*

An AI agent can retrieve a number from a database and still give the wrong business answer.

Ask an agent for October revenue. It may find invoice amounts, add them, and return a convincing total. But does revenue mean booked orders, paid invoices, recognized revenue, or cash collected? Were credits deducted? Which legal entity owns the records? Does the user have permission to see the underlying data?

The model can generate SQL. That does not make it the authority on business semantics.

This is where enterprise agent architecture needs to evolve: **business context should be a governed service, not a collection of definitions reconstructed independently by every agent.**

## Why this topic matters now

On October 20, Neo4j announced Context Engine, a shared business-knowledge layer combining ontologies, retrieval, governance, and memory. It remains in **private preview**. The same day, ARIS announced Process Context for Enterprise AI, linking process definitions, roles, risks, and controls through MCP, with availability stated from October 26. On October 26, Interact announced an MCP interface for workplace knowledge and actions tied to employee permissions; its **full availability is planned for later in 2026**.

These are vendor announcements, not independent proof that any one product solves the problem. Nevertheless, they expose a common architectural requirement: agents need business meaning and authorization context in addition to raw data.

My preferred design principle is simple: **the agent asks for a business metric; the semantic service owns its definition, data access rules, and evidence.**

## 1. Separate reasoning from metric authority

Consider a finance analyst asking:

> What was our net revenue in October, and which records support it?

A weak implementation lets the LLM invent a SQL query over whichever tables it can access. The result may look correct while silently including draft invoices, missing credits, or crossing tenant boundaries.

A stronger architecture uses fixed, approved metric definitions exposed as tools.

```text
User question
    |
    v
LLM / deterministic planner
    |
    v
Agent orchestrator (tool selection, trace ID)
    |
    v
MCP client -> MCP semantic-context server
                    |
                    +-- Validate tool arguments
                    +-- Check tenant and scopes
                    +-- Enforce classification
                    +-- Apply versioned metric definition
                    +-- Calculate from governed source rows
                    +-- Record audit decision
                    |
                    v
              Metric + lineage evidence
                    |
                    v
               Agent explanation
```

The model can choose which approved tool to call. It cannot redefine the metric formula or choose another tenant merely by writing a persuasive prompt.

## 2. Define a small semantic contract

The companion implementation uses three MCP tools:

- `describe_metric(metric_id)` returns the approved definition and version.
- `query_metric(metric_id, period)` calculates the metric for the server's tenant.
- `explain_lineage(metric_id, period)` returns the source records contributing to the result.

Our approved `net_revenue` definition is deliberately explicit: **paid invoice amounts minus issued credits; exclude drafts**. The metric has version `1.0` and uses USD.

For fictional tenant `acme`, October contains two paid invoices of $1,250 and $500, a $200 issued credit, and a $9,000 draft invoice. Another tenant has a $9,990 paid invoice.

The correct October result for `acme` is **$1,550**, supported by three source records. The draft and other tenant's invoice must not appear.

This is not GraphRAG. It is a small relational semantic registry with source lineage, chosen so that the control boundary can be inspected without a graph platform.

## 3. Make tenant identity non-negotiable

The dangerous tool design would be:

```python
query_metric(metric_id, period, tenant_id)
```

That allows the model to propose a tenant identifier. A malicious instruction or an innocent mistake could ask for another organization's data.

Instead, our tool accepts only `metric_id` and `period`. The server obtains tenant identity from its trusted launch context, not from model-generated arguments.

The SQL query is parameterized and includes the tenant predicate:

```python
rows = conn.execute("""
    SELECT fact_id, source_system, amount_cents,
           kind, classification
    FROM facts
    WHERE tenant_id = ? AND period = ?
      AND (
        (kind = 'invoice' AND status = 'paid')
        OR (kind = 'credit' AND status = 'issued')
      )
    ORDER BY fact_id
""", (TENANT, period)).fetchall()
```

A tool request that adds `tenant_id='zenith'` is rejected as `invalid_arguments`.

There is an important limitation: this demonstration trusts environment variables supplied by the local launcher. That is not a production identity solution. Real deployments should validate user or workload identity independently, bind scopes to that identity, and enforce access again at the system of record.

## 4. Classification-aware retrieval must fail closed

Row-level filtering is only part of the problem. Data classification can make an apparently valid aggregate unsafe.

Suppose November includes a restricted invoice. If the agent lacks `data.restricted`, simply omitting that row would return a false revenue figure.

Our server takes a conservative approach:

```python
if any(r[4] == "restricted" for r in rows) \
        and "data.restricted" not in SCOPES:
    return deny("classification_denied")
```

The entire calculation is refused rather than presented as a complete result.

Production policy can be more nuanced. Some organizations permit aggregates over restricted data if minimum group sizes or disclosure controls are satisfied. But that must be an explicit business and security decision, not an accidental consequence of retrieval filtering.

This distinction matters in RAG systems too. A vector index can retrieve a relevant passage without proving that the requesting user is entitled to see it.

**Relevance and authorization are separate dimensions.**

## 5. Lineage is evidence, not decoration

The result of `query_metric` includes the metric version, period, tenant, value, currency, and source count.

`explain_lineage` adds the contributing record IDs and signed amounts:

```json
{
  "tenant": "acme",
  "metric_id": "net_revenue",
  "metric_version": "1.0",
  "period": "2026-10",
  "value": "1550.00",
  "unit": "USD",
  "lineage": [
    {"fact_id": "AC-C1", "signed_cents": -20000},
    {"fact_id": "AC-I1", "signed_cents": 125000},
    {"fact_id": "AC-I2", "signed_cents": 50000}
  ]
}
```

This is a shortened illustration; the executable output also identifies source systems.

A model can now explain not just *what* the value is, but *why*. The application can independently verify the arithmetic and investigate the records.

Source identifiers are not automatically safe to disclose. In a real implementation, lineage retrieval needs its own permission, which is why this tool requires `lineage.read` in addition to the metric and data scopes.

## 6. Reproduce the working example

The downloadable project includes `server.py`, `agent.py`, `test_demo.py`, and a README.

**Requirements:** Python 3.11 or later. The offline demo uses only the standard library.

```bash
python agent.py --demo
python -m unittest -v test_demo.py
```

The local run produced these key results:

```text
OCTOBER_REVENUE: ... "value": "1550.00"
TENANT_SPOOF: {"error": "invalid_arguments"}
RESTRICTED_NOVEMBER: {"error": "classification_denied"}
NO_LINEAGE_SCOPE: {"error": "missing_scope:lineage.read"}
AUDIT_ROWS: 6
```

All four automated tests passed locally. They cover metric arithmetic, lineage, tenant isolation, scope enforcement, classification denial, and audit records.

The server speaks a **minimal MCP 2025-11-25 stdio subset**, including initialization, tool discovery, and tool calls. That version uses the older handshake lifecycle; the newer 2026-07-28 specification has a stateless lifecycle. For production, use an official MCP SDK and the protocol revision negotiated with your client.

An optional live model-driven path uses OpenAI's Responses API:

```bash
python -m pip install openai
export OPENAI_API_KEY='your-key'
export OPENAI_MODEL='your-supported-function-calling-model'
python agent.py --live --prompt \
  'Explain October net revenue and its source lineage.'
```

The model proposes function calls. The orchestrator forwards them to MCP, returns structured tool results to the model, and limits the loop to four turns. **This live-model path was not executed**; the tested path is the deterministic offline demonstration.

## 7. What the demo does not solve

The example is intentionally small. SQLite is not a distributed semantic catalog. The audit table is not tamper-evident. Environment scopes are not authenticated delegation. There is no external ERP, no remote transport, no real-time policy revocation, and no production-grade rate limiting or cancellation.

Those omissions define the next engineering steps: verified identity, policy evaluation close to source systems, controlled metric versioning, data-contract testing, immutable audit retention, and tracing across orchestrators and MCP servers.

I would also add tests that compare the semantic service's results with an independent finance-approved calculation. An internally consistent answer can still be wrong if the approved definition is wrong.

## The architectural decision

The industry is beginning to describe context as an enterprise asset. I agree with the direction, but I would be careful not to turn the context platform into another ungoverned copy of every operational system.

Keep business definitions reusable, source permissions authoritative, and evidence traceable. Expose approved capabilities over MCP rather than letting every agent improvise queries and business rules.

**An agent should be free to reason about a metric. It should not be free to redefine what the metric means or whose data it is allowed to use.**

That is the boundary between a useful AI demonstration and an enterprise data architecture capable of supporting many agents consistently.

---

### Sources and verification

1. Neo4j, *Context Engine Launches to Create AI Knowledge Layer*, October 20, 2026 — private preview: https://neo4j.com/press-releases/neo4j-context-engine/
2. ARIS, *Process Context for Enterprise AI*, October 20, 2026 — availability stated from October 26: https://aris.com/newsroom/aris-launches-process-context-for-enterprise-ai/
3. Interact Software, *Interact MCP*, October 26, 2026 — full availability planned later in 2026: https://rss.globenewswire.com/news-release/2026/10/26/3388061/0/en/interact-brings-700-intranet-capabilities-to-enterprise-ai-assistants-with-interact-mcp.html
4. MCP tools specification, 2026-07-28: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx
5. OpenAI, *Function calling documentation*: https://developers.openai.com/api/docs/guides/function-calling
