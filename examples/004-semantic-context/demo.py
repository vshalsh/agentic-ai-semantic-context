"""Run: python demo.py --tenant acme --period 2026-10"""
import argparse
import json
from semantic import Context, SemanticService


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="acme")
    parser.add_argument("--period", default="2026-10")
    args = parser.parse_args()
    service = SemanticService()
    service.seed()
    context = Context("analyst-1", args.tenant, frozenset({"metric.read", "lineage.read"}))
    for name, fields in [
        ("describe_metric", {"metric_id": "net_revenue"}),
        ("query_metric", {"metric_id": "net_revenue", "period": args.period}),
        ("explain_lineage", {"metric_id": "net_revenue", "period": args.period}),
        ("query_metric", {"metric_id": "net_revenue", "period": args.period,
                          "tenant": "other"}),
    ]:
        print(name, json.dumps(service.call(name, fields, context), indent=2))
    print("AUDIT", json.dumps(service.audit_rows(), indent=2))
    service.close()


if __name__ == "__main__":
    main()
