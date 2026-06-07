"""Standard production calculator — 10k traffic/day web app with autoscaling.
Run: python3 standard_calc.py
"""
import asyncio, uuid, re, httpx
from aws_calc_mcp.core import save_estimate
from aws_calc_mcp.services import build
from aws_calc_mcp import compute

def _gid(name):
    return re.sub(r'[^A-Za-z0-9]', '', name) + '-' + str(uuid.uuid4())

# 10k requests/day -> ~300k/month
REGION = "us-east-1"

GROUPS = {
    "Compute (Auto Scaling)": [
        ("EC2", "Baseline 2 instances 24/7", {"instances": 2, "instance_type": "t3.medium", "os": "linux", "storage_gb": 30}),
        ("EC2", "Auto-scaled instances ~5h/day", {"instances": 2, "instance_type": "t3.medium", "os": "linux", "storage_gb": 30, "hours_per_day": 5}),
    ],
    "Networking and Delivery": [
        ("ALB", "Application Load Balancer", {"load_balancers": 1, "data_processed_gb": 50, "requests_per_sec": 1}),
        ("API Gateway", "REST API (~0.3M req/mo)", {"http_requests_million": 0.3, "rest_requests_million": 0.3}),
        ("CloudFront", "CDN for static site", {"data_transfer_gb": 100, "https_requests": 300000}),
        ("S3", "Static website hosting", {"storage_gb": 10, "put_requests": 5000, "get_requests": 300000, "data_returned_gb": 50}),
    ],
    "Database and Storage": [
        ("RDS MySQL", "MySQL 50GB", {"instance_type": "db.t3.medium", "storage_gb": 50, "deployment": "single-az"}),
        ("DynamoDB", "Session/state table", {"mode": "provisioned", "read_capacity": 25, "write_capacity": 25, "storage_gb": 25}),
        ("AWS Backup", "Backup RDS + DynamoDB", {"primary_storage_gb": 100, "daily_change_pct": 5, "daily_retention_days": 30}),
    ],
    "Async Processing": [
        ("SQS", "Job queue", {"requests_million": 0.3}),
        ("Lambda", "Queue consumer", {"requests": 300000, "duration_ms": 500, "memory_mb": 512}),
    ],
    "Security and Audit": [
        ("WAF", "Web ACL on ALB/CloudFront", {"web_acls": 1, "rules_per_acl": 5, "requests_millions": 0.3}),
        ("CloudTrail", "API audit logging", {"write_events_million": 0.3, "data_ingested_gb": 5}),
    ],
}

async def main():
    groups = {}
    for gname, svcs in GROUPS.items():
        gsv = {}
        for svc, desc, cfg in svcs:
            p = build(svc, REGION, desc, cfg)
            gsv[f'{p["serviceCode"]}-{uuid.uuid4()}'] = p
        groups[_gid(gname)] = {"name": gname, "services": gsv}
    draft = await save_estimate("Standard Production Web App (10k/day) + API Gateway", {}, groups)
    final, totals = await compute.bake_costs(draft, timeout_ms=120000)
    d = httpx.get(f'https://d3knqfixx3sbls.cloudfront.net/{final}', timeout=20).json()
    print("TOTAL:", d.get("totalCost"))
    for gid, g in d["groups"].items():
        print(f'\n[{g["name"]}]')
        for sid, s in g["services"].items():
            c = s.get("serviceCost", {}).get("monthly", "MISS")
            print(f'  {s.get("description") or s["serviceCode"]:<35} ${c}')
    print("\nLINK: https://calculator.aws/#/estimate?id=" + final)

if __name__ == "__main__":
    asyncio.run(main())
