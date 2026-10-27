"""Model-independent orchestrator demo; no external dependencies."""
import json
from server import SemanticService

def run_demo():
    service = SemanticService()
    context = {"tenant": "acme", "scopes": {"metric.read", "lineage.read"}}
    metric = service.call("describe_metric", {"metric_id": "net_revenue"}, context)
    result = service.call("query_metric",
                          {"metric_id": "net_revenue", "period": "2026-10"}, context)
    lineage = service.call("explain_lineage",
                           {"metric_id": "net_revenue", "period": "2026-10"}, context)
    print("DEFINITION", json.dumps(metric))
    print("OCTOBER_REVENUE", json.dumps(result))
    print("LINEAGE", json.dumps(lineage))
    print("TENANT_SPOOF", json.dumps(service.call("query_metric",
        {"metric_id": "net_revenue", "period": "2026-10", "tenant": "other"}, context)))
    print("RESTRICTED_NOVEMBER", json.dumps(service.call("query_metric",
        {"metric_id": "net_revenue", "period": "2026-11"}, context)))
    print("AUDIT_ROWS", len(service.audit))

if __name__ == "__main__":
    run_demo()
