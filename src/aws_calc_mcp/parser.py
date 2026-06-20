"""
Natural-language → estimate parser.

Lets users describe infrastructure in plain English instead of writing JSON, e.g.

    "3 t3.large EC2 with 50 GB each, an RDS MySQL db.m5.large 100 GB,
     a 500 GB S3 bucket, CloudFront 1 TB transfer, and an ALB"

It's a pragmatic heuristic parser (no LLM, no API key) covering the most common
services and phrasings. For free-form prose, an MCP client (Claude/ChatGPT) will
still parse more flexibly — but this makes the CLI and REST API prompt-friendly.
Every parse returns the structured services it understood so the user can verify.
"""

import re
import difflib

_NUM_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
}

# Category for each canonical service -> used when the user wants grouping.
_CATEGORY = {
    "ec2": "Compute", "lambda": "Compute", "fargate": "Compute", "eks": "Compute",
    "lightsail": "Compute",
    "s3": "Storage", "ebs": "Storage", "efs": "Storage", "ecr": "Storage",
    "rds mysql": "Database", "rds postgresql": "Database", "rds oracle": "Database",
    "rds sqlserver": "Database", "rds mariadb": "Database", "aurora": "Database",
    "aurora mysql": "Database", "aurora postgresql": "Database", "dynamodb": "Database",
    "redshift": "Database", "opensearch": "Database", "elasticache": "Database",
    "redis": "Database",
    "cloudfront": "Network", "route53": "Network", "api gateway": "Network",
    "alb": "Network", "nlb": "Network", "elb": "Network", "vpc": "Network",
    "nat gateway": "Network", "transit gateway": "Network", "site-to-site vpn": "Network",
    "network firewall": "Network", "privatelink": "Network", "data transfer": "Network",
    "waf": "Security", "guardduty": "Security", "kms": "Security", "cognito": "Security",
    "inspector": "Security", "security hub": "Security",
    "cloudwatch": "Monitoring", "cloudtrail": "Monitoring", "config": "Monitoring",
    "sqs": "Messaging", "sns": "Messaging", "ses": "Messaging", "kinesis": "Messaging",
    "codebuild": "DevTools", "codepipeline": "DevTools",
    "bedrock": "AI/ML",
    "aws backup": "Backup & DR", "edr": "Backup & DR",
}

# Common misspellings / variants -> a token the fuzzy matcher recognises.
_FUZZY_TOKENS = {
    "ec2": "ec2", "lambda": "lambda", "lamda": "lambda", "lambda": "lambda",
    "s3": "s3", "bucket": "s3", "buckit": "s3",
    "ec2": "ec2", "rds": "rds", "dynamodb": "dynamodb", "dynamo": "dynamodb",
    "dynmodb": "dynamodb", "cloudfront": "cloudfront", "cloudfornt": "cloudfront",
    "cdn": "cloudfront", "fargate": "fargate", "farget": "fargate",
    "lightsail": "lightsail", "redshift": "redshift", "opensearch": "opensearch",
    "elasticache": "elasticache", "redis": "redis", "memcached": "memcached",
    "cloudwatch": "cloudwatch", "cloudtrail": "cloudtrail", "guardduty": "guardduty",
    "cognito": "cognito", "kinesis": "kinesis", "aurora": "aurora", "ebs": "ebs",
    "efs": "efs", "ecr": "ecr", "eks": "eks", "kubernetes": "eks", "sqs": "sqs",
    "sns": "sns", "ses": "ses", "waf": "waf", "kms": "kms", "vpc": "vpc",
    "cloudfrnt": "cloudfront", "postgres": "rds", "postgresql": "rds", "mysql": "rds",
    "bedrock": "bedrock", "route53": "route53", "alb": "alb", "nlb": "nlb",
    "backup": "backup", "datatransfer": "data transfer",
}
_FUZZY_TO_SERVICE = {
    "ec2": "ec2", "lambda": "lambda", "s3": "s3", "bucket": "s3", "rds": "rds mysql",
    "dynamodb": "dynamodb", "cloudfront": "cloudfront", "fargate": "fargate",
    "lightsail": "lightsail", "redshift": "redshift", "opensearch": "opensearch",
    "elasticache": "elasticache", "redis": "redis", "memcached": "elasticache",
    "cloudwatch": "cloudwatch", "cloudtrail": "cloudtrail", "guardduty": "guardduty",
    "cognito": "cognito", "kinesis": "kinesis", "aurora": "aurora", "ebs": "ebs",
    "efs": "efs", "ecr": "ecr", "eks": "eks", "sqs": "sqs", "sns": "sns",
    "ses": "ses", "waf": "waf", "kms": "kms", "vpc": "vpc", "bedrock": "bedrock",
    "route53": "route53", "alb": "alb", "nlb": "nlb", "backup": "aws backup",
    "data transfer": "data transfer", "datatransfer": "data transfer",
}

# service keyword -> canonical builder name in services._SERVICES
_KEYWORDS = [
    (r"\baurora\s+postgres\w*", "aurora postgresql"),
    (r"\baurora\s+mysql", "aurora mysql"),
    (r"\baurora\b", "aurora"),
    (r"\brds\s+postgres\w*", "rds postgresql"),
    (r"\brds\s+mysql", "rds mysql"),
    (r"\brds\s+oracle", "rds oracle"),
    (r"\brds\s+(sql\s*server|mssql)", "rds sqlserver"),
    (r"\brds\s+mariadb", "rds mariadb"),
    (r"\b(rds|relational database)\b", "rds mysql"),
    (r"\bdynamo\s?db\b", "dynamodb"),
    (r"\bredshift\b", "redshift"),
    (r"\bopensearch\b|\belasticsearch\b", "opensearch"),
    (r"\b(elasticache|memcached)\b", "elasticache"),
    (r"\bredis\b", "redis"),
    (r"\blambdas?\b|\bfunctions?\b", "lambda"),
    (r"\bfargate\b", "fargate"),
    (r"\beks\b|\bkubernetes\b|\bk8s\b", "eks"),
    (r"\blightsail\b", "lightsail"),
    (r"\bbedrock\b", "bedrock"),
    (r"\bcloud\s?front\b|\bcdn\b", "cloudfront"),
    (r"\bapi\s*gateway\b", "api gateway"),
    (r"\broute\s*53\b", "route53"),
    (r"\b(alb|application load balancer)\b", "alb"),
    (r"\b(nlb|network load balancer)\b", "nlb"),
    (r"\b(elb|load balancer)\b", "elb"),
    (r"\bnat\s*gateway\b", "nat gateway"),
    (r"\btransit\s*gateway\b", "transit gateway"),
    (r"\baws\s*data\s*transfer\b|\bdata\s*transfer\b", "data transfer"),
    (r"\b(site[- ]to[- ]site\s*vpn|vpn)\b", "site-to-site vpn"),
    (r"\bnetwork firewall\b", "network firewall"),
    (r"\bprivatelink\b|\bvpc endpoint", "privatelink"),
    (r"\bvpc\b", "vpc"),
    (r"\bs3\b|\bbuckets?\b|\bobject storage\b", "s3"),
    (r"\bebs\b|\bblock storage\b", "ebs"),
    (r"\befs\b|\bfile system\b", "efs"),
    (r"\becr\b|\bcontainer registry\b", "ecr"),
    (r"\bsqs\b|\bqueues?\b", "sqs"),
    (r"\bsns\b|\bnotification", "sns"),
    (r"\bses\b|\bemail\b", "ses"),
    (r"\bkinesis\b", "kinesis"),
    (r"\bcloudwatch\b", "cloudwatch"),
    (r"\bcloudtrail\b", "cloudtrail"),
    (r"\bconfig\b", "config"),
    (r"\bwaf\b", "waf"),
    (r"\bguard\s*duty\b", "guardduty"),
    (r"\binspector\b", "inspector"),
    (r"\bsecurity hub\b", "security hub"),
    (r"\bkms\b|\bkey management\b", "kms"),
    (r"\bcognito\b", "cognito"),
    (r"\bcodebuild\b", "codebuild"),
    (r"\bcodepipeline\b", "codepipeline"),
    (r"\bbackup\b", "aws backup"),
    (r"\b(elastic\s+disaster\s+recovery|disaster recovery|\bdrs\b|\bedr\b)", "edr"),
    (r"\bec2\b|\binstances?\b|\bvms?\b|\bservers?\b", "ec2"),
    # vague-intent words (low priority; specific names above always win)
    (r"\bweb\s?app\b|\bweb\s?site\b|\bwebsite\b", "ec2"),
    (r"\bdatabase\b", "rds mysql"),
]

_DEFAULT_REGION = "us-east-1"
_REGION_HINTS = {
    "mumbai": "ap-south-1", "ap-south-1": "ap-south-1",
    "hyderabad": "ap-south-2", "ap-south-2": "ap-south-2",
    "virginia": "us-east-1", "us-east-1": "us-east-1",
    "ohio": "us-east-2", "us-east-2": "us-east-2",
    "oregon": "us-west-2", "us-west-2": "us-west-2",
    "ireland": "eu-west-1", "eu-west-1": "eu-west-1",
    "frankfurt": "eu-central-1", "eu-central-1": "eu-central-1",
    "london": "eu-west-2", "singapore": "ap-southeast-1", "ap-southeast-1": "ap-southeast-1",
    "tokyo": "ap-northeast-1", "sydney": "ap-southeast-2",
}


def _num(token: str) -> float:
    token = token.lower().replace(",", "").strip()
    m = re.match(r"^([\d.]+)\s*(k|m|million|thousand|bn|billion)?$", token)
    if not m:
        return _NUM_WORDS.get(token, 0)
    val = float(m.group(1))
    mult = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6,
            "bn": 1e9, "billion": 1e9}.get(m.group(2), 1)
    return val * mult


def _qty(clause: str) -> int:
    """Leading count, e.g. '3 ec2', 'two lambdas'. Ignores sizes/instance types."""
    # remove things whose numbers are NOT counts: instance types (m6i.2xlarge),
    # sizes (500 GB), request counts (2M requests), and bare 'NxlargE'.
    c = _INSTANCE_RE.sub(" ", clause)
    c = re.sub(r"\b\d[\d.]*\s*(gb|tb|mb|kb|gib|tib|ghz|mhz)\b", " ", c)
    c = re.sub(r"\b\d[\d.]*\s*(hours?|hrs?|days?|weeks?|months?)\b", " ", c)
    c = re.sub(r"\b\d[\d.,]*\s*(k|m|million|thousand|bn|billion)?\s*"
               r"(requests?|req|messages?|msgs?|invocations?|calls?|hits?|events?|tokens?|users?|maus?)\b", " ", c)
    c = re.sub(r"\b\d+\s*x?large\b|\bxlarge\b", " ", c)
    c = re.sub(r"\b(20\d\d|19\d\d)\b", " ", c)   # drop years like 2019/2022
    m = re.search(r"\b(\d+|" + "|".join(_NUM_WORDS) + r")\s+"
                  r"(nodes?|instances?|servers?|vms?|tasks?|clusters?|volumes?)\b", c)
    if m:
        n = _num(m.group(1)) if m.group(1).isdigit() else _NUM_WORDS.get(m.group(1), 1)
        if 0 < n <= 1000:
            return int(n)
    m = re.search(r"\b(\d+|" + "|".join(_NUM_WORDS) + r")\s*(?:x\s*)?(?=[a-z])", c)
    if m:
        n = _num(m.group(1)) if m.group(1).isdigit() else _NUM_WORDS.get(m.group(1), 1)
        if 0 < n <= 1000:
            return int(n)
    m = re.search(r"\b(\d+)\s*x\b", c)
    return int(m.group(1)) if m else 1


def _storage_gb(clause: str):
    m = re.search(r"(\d[\d.]*)\s*(gb|tb|mb)\b", clause)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2)
    return int(val * 1024) if unit == "tb" else (round(val / 1024, 2) if unit == "mb" else int(val))


def _transfer_gb(clause: str):
    """A GB/TB figure tied to data transfer / outbound / egress wording."""
    m = (re.search(r"(?:data\s*transfer|transfer|outbound|egress)[^.,;]*?(\d[\d.]*)\s*(gb|tb)", clause)
         or re.search(r"(\d[\d.]*)\s*(gb|tb)[^.,;]*?(?:data\s*transfer|transfer|outbound|egress)", clause))
    if not m:
        return None
    val = float(m.group(1))
    return int(val * 1024) if m.group(2) == "tb" else int(val)


def _requests_per_month(clause: str):
    """Find a request/message/invocation count and normalize to per-month."""
    m = re.search(r"(\d[\d.,]*)\s*(k|m|million|thousand|bn|billion)?\s*"
                  r"(requests?|req|messages?|msgs?|invocations?|calls?|hits?|events?)"
                  r"\s*(?:per\s*|/)?\s*(day|month|week|hour|sec(?:ond)?|min(?:ute)?)?", clause)
    if not m:
        return None
    n = _num(f"{m.group(1)}{m.group(2) or ''}")
    period = (m.group(4) or "month").lower()
    factor = {"day": 30, "week": 4.345, "month": 1, "hour": 730,
              "sec": 2_592_000, "second": 2_592_000, "min": 43_200, "minute": 43_200}.get(period, 1)
    return int(n * factor)


_INSTANCE_RE = re.compile(r"\b((?:db\.|cache\.)?[a-z]+\d+[a-z]*\.(?:nano|micro|small|medium|large|\d*xlarge|search))\b")


def _hours_per_month(clause: str):
    """Find explicit partial-run time, preserving AWS's Hours/Month unit when given."""
    m = re.search(r"(\d[\d.]*)\s*(?:hours?|hrs?)\s*(?:per\s*|/)?\s*month", clause)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d[\d.]*)\s*(?:hours?|hrs?)\s*(?:per\s*|/)?\s*day", clause)
    if m:
        return round(float(m.group(1)) * 30, 2)
    return None


def _instance_type(clause: str):
    m = _INSTANCE_RE.search(clause)
    return m.group(1) if m else None


def _normalize_clause(c: str) -> str:
    """Collapse phrasings so 'RDS Aurora MySQL' = Aurora, drop 'amazon/aws' noise."""
    c = re.sub(r"\brds\s+aurora\b", "aurora", c)   # 'RDS Aurora' -> Aurora
    c = re.sub(r"\b(amazon|aws)\s+", "", c)
    return re.sub(r"\s+", " ", c).strip()


def _service_matches(clause: str):
    """All distinct, non-overlapping service mentions in a clause, left to right."""
    spans = []
    for pat, name in _KEYWORDS:
        for m in re.finditer(pat, clause):
            spans.append([m.start(), m.end(), name])
    # longest match wins at any position (specific over generic)
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    kept = []
    for s in spans:
        if any(not (s[1] <= k[0] or s[0] >= k[1]) for k in kept):
            continue
        kept.append(s)
    kept.sort(key=lambda s: s[0])
    return kept


def _detect_service(clause: str, itype: str | None):
    # instance type can imply the service even without a keyword
    if itype:
        if itype.startswith("db."):
            for pat, name in _KEYWORDS:
                if name.startswith(("rds", "aurora")) and re.search(pat, clause):
                    return name
            return "rds mysql"
        if itype.startswith("cache."):
            return "redis" if "redis" in clause else "elasticache"
        if itype.endswith(".search"):
            return "opensearch"
    for pat, name in _KEYWORDS:
        if re.search(pat, clause):
            return name
    if itype:
        return "ec2"
    # fuzzy fallback — tolerate spelling mistakes ("lamda", "buckit", "dynmodb")
    tokens = re.findall(r"[a-z0-9]+", clause)
    for tok in tokens:
        if len(tok) < 2:
            continue
        hit = difflib.get_close_matches(tok, _FUZZY_TO_SERVICE.keys(), n=1, cutoff=0.82)
        if hit:
            return _FUZZY_TO_SERVICE[hit[0]]
    return None


def group_services(services: list[dict]) -> list[dict]:
    """Turn a flat services list into category groups (Compute, Database, …)."""
    buckets: dict[str, list] = {}
    order: list[str] = []
    for s in services:
        cat = _CATEGORY.get(s.get("service", ""), "Other")
        if cat not in buckets:
            buckets[cat] = []
            order.append(cat)
        buckets[cat].append(s)
    return [{"group_name": cat, "services": buckets[cat]} for cat in order]


def _add_snapshot(cfg: dict, clause: str) -> None:
    """Detect 'daily/weekly/monthly snapshot' (+ optional GB changed) in a clause."""
    if "snapshot" not in clause:
        return
    if re.search(r"\bweekly\b", clause):
        freq = "weekly"
    elif re.search(r"\bmonthly\b", clause):
        freq = "monthly"
    else:
        freq = "daily"   # 'snapshot' with no cadence -> assume daily
    # only an amount stated AFTER 'snapshot' is the per-snapshot change; a GB before
    # it ("50GB storage ... snapshot") is the volume size, not the snapshot delta.
    m = re.search(r"snapshot\w*\s*(?:of\s*|each\s*)?(\d[\d.]*)\s*(gb|tb)", clause)
    amt = int(float(m.group(1)) * (1024 if m.group(2) == "tb" else 1)) if m else None
    cfg["snapshot_frequency"] = freq
    cfg["snapshot_changed_gb"] = amt if amt is not None else 10  # assume 10 GB/snapshot


def _config_for(name: str, clause: str, itype: str | None, qty: int) -> dict:
    gb = _storage_gb(clause)
    reqs = _requests_per_month(clause)
    cfg: dict = {}

    if name == "ec2":
        cfg["instances"] = qty
        if itype:
            cfg["instance_type"] = itype
        # storage = a GB figure NOT tied to transfer wording
        sg = _storage_gb(re.sub(r"(?:data\s*transfer|transfer|outbound|egress)[^.,;]*", "", clause))
        cfg["storage_gb"] = sg or 30
        tg = _transfer_gb(clause)
        if tg:
            cfg["data_outbound_gb"] = tg
        hours = _hours_per_month(clause)
        if hours:
            cfg["hours_per_month"] = int(hours) if hours.is_integer() else hours
        if re.search(r"\b(3\s*yr|3-year|three year)\b", clause):
            cfg.update(pricing="compute-savings", term="3yr")
        elif re.search(r"\b(1\s*yr|1-year|one year|reserved|savings)\b", clause):
            cfg.update(pricing="compute-savings", term="1yr")
        _add_snapshot(cfg, clause)
    elif name == "lambda":
        cfg["requests"] = reqs or 1_000_000
        cfg["duration_ms"] = 200
        cfg["memory_mb"] = 512
    elif name == "fargate":
        cfg["tasks"] = qty
        cfg["vcpu"] = 1
        cfg["memory_gb"] = 2
    elif name == "eks":
        cfg["clusters"] = qty
    elif name == "s3":
        cfg["storage_gb"] = gb or 100
        if reqs:
            cfg["get_requests"] = reqs
    elif name in ("ebs",):
        cfg["volumes"] = qty
        cfg["storage_gb"] = gb or 100
        _add_snapshot(cfg, clause)
    elif name == "efs":
        cfg["storage_gb"] = gb or 100
    elif name == "ecr":
        cfg["storage_gb"] = gb or 10
    elif name.startswith(("rds", "aurora")):
        if name.startswith("rds"):
            cfg["instance_type"] = itype or "db.m5.large"
            cfg["storage_gb"] = gb or 100
            if "multi" in clause:
                cfg["deployment"] = "multi-az"
        else:
            cfg["instance_type"] = itype or "db.r6g.large"
            cfg["nodes"] = qty
    elif name == "dynamodb":
        cfg["mode"] = "on-demand" if "on-demand" in clause or "on demand" in clause else "provisioned"
        if cfg["mode"] == "provisioned":
            cfg.update(read_capacity=25, write_capacity=25)
        if gb:
            cfg["storage_gb"] = gb
    elif name == "redshift":
        cfg["nodes"] = qty
        cfg["node_type"] = itype or "ra3.xlplus"
    elif name == "opensearch":
        cfg["nodes"] = qty
        cfg["instance_type"] = itype or "r5.large.search"
    elif name in ("elasticache", "redis"):
        cfg["nodes"] = qty
        cfg["node_type"] = itype or "cache.m5.large"
        cfg["engine"] = "redis" if name == "redis" else "redis"
    elif name == "cloudfront":
        cfg["data_transfer_gb"] = _transfer_gb(clause) or gb or 100
        cfg["https_requests"] = reqs or 1_000_000
    elif name == "data transfer":
        tg = _transfer_gb(clause) or gb or 100
        if "inbound" in clause or "ingress" in clause:
            cfg["data_inbound_gb"] = tg
        elif "intra" in clause or "inter" in clause or "regional" in clause:
            cfg["data_intra_region_gb"] = tg
        else:
            cfg["data_outbound_gb"] = tg
    elif name == "api gateway":
        cfg["http_requests_million"] = round((reqs or 1_000_000) / 1e6, 4)
    elif name == "route53":
        cfg["hosted_zones"] = qty
        if reqs:
            cfg["queries_million"] = round(reqs / 1e6, 4)
    elif name in ("alb", "nlb", "elb"):
        cfg["load_balancers"] = qty
        cfg["data_processed_gb"] = gb or 100
    elif name in ("sqs",):
        cfg["requests_million"] = round((reqs or 1_000_000) / 1e6, 4)
    elif name == "sns":
        cfg["notifications_million"] = round((reqs or 1_000_000) / 1e6, 4)
    elif name == "ses":
        cfg["emails_sent_thousand"] = round((reqs or 100_000) / 1e3, 2)
    elif name == "kinesis":
        cfg["records_per_second"] = 1000
        cfg["record_size_kb"] = 5
    elif name == "cloudwatch":
        cfg.update(metrics=50, logs_gb=gb or 50)
    elif name == "cloudtrail":
        cfg.update(write_events_million=1, data_ingested_gb=gb or 5)
    elif name == "waf":
        cfg.update(web_acls=qty, rules_per_acl=10,
                   requests_millions=round((reqs or 1_000_000) / 1e6, 4))
    elif name == "guardduty":
        cfg.update(s3_data_gb=gb or 100, management_events_million=1)
    elif name == "kms":
        cfg.update(keys=qty, symmetric_requests=reqs or 100_000)
    elif name == "cognito":
        cfg["maus"] = int(reqs) if reqs else 50_000
    elif name in ("nat gateway",):
        cfg.update(gateways=qty, nat_data_gb=gb or 100)
    elif name == "transit gateway":
        cfg.update(attachments=qty, tgw_data_gb=gb or 100)
    elif name == "site-to-site vpn":
        cfg["connections"] = qty
    elif name == "network firewall":
        cfg.update(endpoints=qty, data_processed_gb=gb or 100)
    elif name == "privatelink":
        cfg.update(endpoints=qty)
    elif name == "vpc":
        cfg.update(public_ips=qty)
    elif name == "aws backup":
        cfg.update(daily_change_pct=5, annual_growth_pct=10)
    elif name == "edr":
        server_m = re.search(r"\b(\d+|" + "|".join(_NUM_WORDS) + r")\s+"
                             r"(?:source\s+|on[- ]?prem(?:ise)?\s+)?servers?\b", clause)
        disk_m = re.search(r"\b(\d+|" + "|".join(_NUM_WORDS) + r")\s+disks?\b", clause)
        cfg["source_servers"] = int(_num(server_m.group(1))) if server_m else 1
        cfg["storage_gb"] = gb or 500
        if disk_m:
            cfg["disks"] = int(_num(disk_m.group(1)))
        elif "disk" in clause:
            cfg["disks"] = qty
        change_m = re.search(r"\b(\d[\d.]*)\s*(?:%|percent)?\s*change\s*rate\b|"
                             r"\bchange\s*rate\s*(?:of\s*)?(\d[\d.]*)\s*(?:%|percent)?\b", clause)
        if change_m:
            cfg["change_rate_pct"] = float(change_m.group(1) or change_m.group(2))
    elif name == "codebuild":
        cfg["builds_per_month"] = 100
    elif name == "lightsail":
        cfg.update(instances=qty, bundle="medium")
    elif name == "bedrock":
        cfg.update(requests_per_min=100, input_tokens=1000, output_tokens=1000)
    return cfg


# clauses that are just glue/filler — not "unrecognized services"
_FILLER = re.compile(r"^(i (need|want|have|would like)|need|want|please|setup|set up|"
                     r"a |an |the |some |for |in |with |to |and |of |on |our |my |use |"
                     r"infra(structure)?|stack|app|application|each|per month|monthly|"
                     r"on[- ]?demand|reserved|spot|savings?|pricing|generate|create|estimate|link)+$")


def parse_prompt(text: str) -> tuple[list[dict], list[str], list[str]]:
    """
    Parse a natural-language description into a list of service entries.
    Returns (services, notes, unknown) — `unknown` lists clauses we couldn't map
    to a service so callers can tell the user what was skipped.
    """
    if not text:
        return [], [], []
    region = _DEFAULT_REGION
    low = text.lower()
    for hint, code in _REGION_HINTS.items():
        if hint in low:
            region = code
            break

    services: list[dict] = []
    notes: list[str] = []
    unknown: list[str] = []
    # Split on commas / "and" / newlines / semicolons. Also split on "with a/an/the"
    # (introduces another service, e.g. "sqs with a lambda") but NOT "with 50 GB"
    # (an attribute), so sizes stay attached to their service.
    # split on commas / "and" / sentence breaks (". " — not the dot in m6i.2xlarge,
    # which has no trailing space) / "with a|an|the".
    clauses = re.split(r",|\band\b|\bplus\b|;|\n|\.\s+|\bwith\s+an?\s|\bwith\s+the\s", low)

    def _emit(name: str, segment: str):
        itype = _instance_type(segment)
        qty = _qty(segment)
        cfg = _config_for(name, segment, itype, qty)
        services.append({"service": name, "region": region,
                         "description": segment.strip()[:80], "config": cfg})

    last_ec2 = None   # most recent EC2, so "...500GB EBS" folds into it as storage
    for raw in clauses:
        clause = _normalize_clause(raw.strip())
        if len(clause) < 2:
            continue
        matches = _service_matches(clause)
        if not matches:
            # fall back: instance type implies EC2, or fuzzy-match a misspelling
            itype = _instance_type(clause)
            name = _detect_service(clause, itype)
            if name:
                _emit(name, clause)
                if name == "ec2":
                    last_ec2 = services[-1]
            elif "snapshot" in clause:
                pass   # snapshot is an attribute, applied to the server below
            elif re.search(r"pricing|on[- ]?demand|reserved|spot|savings?|"
                           r"hours?\s*(per|/)\s*month|hours?\s*(per|/)\s*day|"
                           r"generate|calculator|estimate|link|account", clause):
                pass   # meta / pricing directive, not a service
            else:
                stripped = clause.strip(" .")
                if re.search(r"[a-z]", stripped) and not _FILLER.match(stripped):
                    unknown.append(raw.strip()[:60])
            continue
        # one or more services in this clause -> slice it per service so each gets
        # its nearby attributes (e.g. "ALB NLB cloudfront 1TB" -> 3 services).
        bounds = [0] + [m[0] for m in matches[1:]] + [len(clause)]
        by_name: dict[str, dict] = {}
        for i, (st, en, name) in enumerate(matches):
            seg = clause[bounds[i]:bounds[i + 1]]
            cfg = _config_for(name, seg, _instance_type(seg), _qty(seg))
            if name == "ec2" and cfg.get("instances", 1) == 1:
                clause_qty = _qty(clause)
                if clause_qty > 1:
                    cfg["instances"] = clause_qty
            entry = {"service": name, "region": region,
                     "description": seg.strip()[:80], "config": cfg}
            if name not in by_name or len(cfg) > len(by_name[name]["config"]):
                by_name[name] = entry

        # "<server>, 500GB EBS volume" -> the EBS is the server's storage, not a
        # separate volume service. Fold a storage-only EBS into the preceding EC2.
        if set(by_name) == {"ebs"} and last_ec2 is not None \
                and "storage_gb" not in last_ec2["config"] \
                and by_name["ebs"]["config"].get("volumes", 1) <= 1 \
                and re.search(r"\b(ebs|volume)\b", clause):
            last_ec2["config"]["storage_gb"] = by_name["ebs"]["config"].get("storage_gb", 30)
            continue

        services.extend(by_name.values())
        if "ec2" in by_name:
            last_ec2 = by_name["ec2"]

    # Operating system + SQL Server edition apply to every EC2 in the request.
    base = ("windows" if "windows" in low else
            "rhel" if ("rhel" in low or "red hat" in low) else
            "suse" if "suse" in low else
            "ubuntu pro" if "ubuntu" in low else None)
    sql = None
    if re.search(r"sql\s*server|mssql", low):
        sql = ("ent" if "enterprise" in low else "web" if "sql server web" in low else "std")
    if base or sql:
        osval = (base or "linux") + (f"-{sql}" if sql else "")
        for s in services:
            if s["service"] == "ec2":
                s["config"]["os"] = osval

    # Pricing/time clauses are often split away from the EC2 clause
    # ("... EC2 with 100GB and 1-year savings plan"). Apply them globally.
    global_hours = _hours_per_month(low)
    global_term = None
    if re.search(r"\b(3\s*yr|3-year|three year)\b", low):
        global_term = "3yr"
    elif re.search(r"\b(1\s*yr|1-year|one year|reserved|savings)\b", low):
        global_term = "1yr"
    for s in services:
        if s["service"] != "ec2":
            continue
        if global_hours and "hours_per_month" not in s["config"]:
            s["config"]["hours_per_month"] = int(global_hours) if global_hours.is_integer() else global_hours
        if global_term and "pricing" not in s["config"]:
            s["config"].update(pricing="compute-savings", term=global_term)

    # drop a bare EC2 spawned by preamble ("...EC2 instances...") when real,
    # detailed servers were also found.
    detailed = any(s["service"] == "ec2" and ("instance_type" in s["config"] or "storage_gb" in s["config"])
                   for s in services)
    if detailed:
        services = [s for s in services if not (
            s["service"] == "ec2" and "instance_type" not in s["config"]
            and "storage_gb" not in s["config"] and s["config"].get("instances", 1) <= 1)]

    # snapshots are commonly described separately ("...and daily snapshot of 20GB").
    # Attach any snapshot spec to the EC2/EBS services that don't already have one.
    if "snapshot" in low:
        for s in services:
            if s["service"] in ("ec2", "ebs") and "snapshot_frequency" not in s["config"]:
                _add_snapshot(s["config"], low)

    # build the human-readable notes AFTER all post-processing so they reflect
    # everything that was applied (e.g. snapshots attached from a separate clause).
    notes = [f"{s['service']} ({', '.join(f'{k}={v}' for k, v in s['config'].items()) or 'defaults'})"
             for s in services]
    return services, notes, unknown
