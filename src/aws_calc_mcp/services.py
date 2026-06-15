"""
AWS Pricing Calculator — exact service payload builders.
All field names verified against real API captures from calculator.aws
"""

import uuid

# ── Regions ─────────────────────────────────────────────────────────────────

REGIONS = {
    "us-east-1": "US East (N. Virginia)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "ca-central-1": "Canada (Central)",
    "ca-west-1": "Canada West (Calgary)",
    "eu-west-1": "Europe (Ireland)",
    "eu-west-2": "Europe (London)",
    "eu-west-3": "Europe (Paris)",
    "eu-central-1": "Europe (Frankfurt)",
    "eu-north-1": "Europe (Stockholm)",
    "eu-south-1": "Europe (Milan)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-south-2": "Asia Pacific (Hyderabad)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-northeast-3": "Asia Pacific (Osaka)",
    "ap-east-1": "Asia Pacific (Hong Kong)",
    "sa-east-1": "South America (Sao Paulo)",
    "me-south-1": "Middle East (Bahrain)",
    "me-central-1": "Middle East (UAE)",
    "af-south-1": "Africa (Cape Town)",
    "il-central-1": "Israel (Tel Aviv)",
    "mx-central-1": "Mexico (Central)",
}

_REV = {v.lower(): k for k, v in REGIONS.items()}


def resolve_region(r: str) -> tuple[str, str]:
    code = r.lower().strip()
    if code in REGIONS:
        return code, REGIONS[code]
    name = _REV.get(code)
    if name:
        return name, REGIONS[name]
    return "us-east-1", REGIONS["us-east-1"]


def uid(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


# EBS snapshot frequency -> snapshots per month (the value the calculator expects).
_SNAP_FREQ = {"daily": "30", "weekly": "4", "monthly": "1", "none": "0", "off": "0", "no": "0"}


def _snapshot(c: dict) -> tuple[str, str | None]:
    """Return (frequency_per_month, changed_gb) from config keys
    snapshot_frequency (daily|weekly|monthly|<n>) and snapshot_changed_gb / snapshot_gb."""
    f = str(c.get("snapshot_frequency", c.get("snapshots", "none"))).lower().strip()
    freq = _SNAP_FREQ.get(f, f if f.isdigit() else "0")
    amt = c.get("snapshot_changed_gb", c.get("snapshot_gb"))
    return freq, (str(amt) if amt is not None else None)


# ── EC2 ─────────────────────────────────────────────────────────────────────
# Verified: all fields from real API capture

def ec2(region="us-east-1", description=None, **c) -> dict:
    """
    instances, instance_type, os, tenancy, workload,
    pricing (on-demand|savings-plans|reserved|spot),
    storage_type (gp3|gp2|io1), storage_gb, data_inbound_gb, data_outbound_gb
    """
    rc, rn = resolve_region(region)
    n = str(c.get("instances", 1))
    os_map = {
        "linux": "linux", "windows": "windows", "rhel": "rhel",
        "suse": "suse", "ubuntu": "ubuntu pro", "ubuntu pro": "ubuntu pro",
        # combined OS + SQL Server tiers (selectedOS values from the calculator)
        "windows-std": "windows-std", "windows-web": "windows-web", "windows-ent": "windows-ent",
        "linux-std": "linux-std", "linux-web": "linux-web", "linux-ent": "linux-ent",
        "rhel-std": "rhel-std", "rhel-web": "rhel-web", "rhel-ent": "rhel-ent",
    }
    wl_map = {"constant": "consistent", "consistent": "consistent",
              "daily": "daily", "weekly": "weekly", "monthly": "monthly"}
    st_map = {
        "gp3": "Storage General Purpose gp3 GB Mo",
        "gp2": "Storage General Purpose gp2 GB Mo",
        "io1": "Storage Provisioned IOPS SSD io1 GB Mo",
        "io2": "Storage Provisioned IOPS SSD io2 GB Mo",
        "st1": "Storage Throughput Optimized HDD GB Mo",
        "sc1": "Storage Cold HDD GB Mo",
    }
    pricing = c.get("pricing", "on-demand").lower().replace("_", "-").replace(" ", "-")
    pr_opt_map = {
        "on-demand": "on-demand", "ondemand": "on-demand",
        "savings-plans": "compute-savings", "savings": "compute-savings",
        "compute-savings": "compute-savings", "compute-savings-plans": "compute-savings",
        "instance-savings": "instance-savings", "instance-savings-plans": "instance-savings",
        "reserved": "standard-reserved", "standard-reserved": "standard-reserved",
        "reserved-instance": "standard-reserved", "ri": "standard-reserved",
        "convertible-reserved": "convertible-reserved", "convertible": "convertible-reserved",
        "spot": "spot",
    }
    pr_opt = pr_opt_map.get(pricing, "on-demand")

    # term: accept "1yr"/"1 year"/"1"/3yr etc -> "1 Year" | "3 Year"
    term_raw = str(c.get("term", "1 Year")).lower()
    term = "3 Year" if "3" in term_raw else "1 Year"
    # upfront: none|partial|all
    up_raw = str(c.get("upfront", "no")).lower()
    upfront = "All" if "all" in up_raw else ("Partial" if "partial" in up_raw else "None")

    if pr_opt == "compute-savings":
        ps = {"selectedOption": "compute-savings", "term": term, "upfrontPayment": upfront, "model": "computeSavings"}
    elif pr_opt == "instance-savings":
        ps = {"selectedOption": "instance-savings", "term": term, "upfrontPayment": upfront, "model": "instanceSavings"}
    elif pr_opt == "standard-reserved":
        ps = {"selectedOption": "standard-reserved", "term": term, "upfrontPayment": upfront}
    elif pr_opt == "convertible-reserved":
        ps = {"selectedOption": "convertible-reserved", "term": term, "upfrontPayment": upfront}
    elif pr_opt == "spot":
        ps = {"selectedOption": "spot", "term": "1 year",
              "utilizationValue": "100", "utilizationUnit": "%Utilized/Month"}
    else:
        # on-demand. utilization can model partial-time / autoscaling instances:
        # either utilization (%) directly, or hours_per_day -> % of 24h.
        if c.get("hours_per_day"):
            util = str(round(float(c["hours_per_day"]) / 24.0 * 100, 1))
        else:
            util = str(c.get("utilization", 100))
        ps = {"selectedOption": "on-demand", "term": "1 year",
              "utilizationValue": util, "utilizationUnit": "%Utilized/Month"}

    in_val  = str(c.get("data_inbound_gb",  ""))
    out_val = str(c.get("data_outbound_gb", ""))
    in_unit  = "gb_month" if c.get("data_inbound_gb")  else "tb_month"
    out_unit = "gb_month" if c.get("data_outbound_gb") else "tb_month"

    calc = {
        "tenancy":           {"value": c.get("tenancy", "shared")},
        "selectedOS":        {"value": os_map.get(c.get("os", "linux").lower(), "linux")},
        "workloadSelection": {"value": wl_map.get(c.get("workload", "constant").lower(), "consistent")},
        "storageType":       {"value": st_map.get(c.get("storage_type", "gp3").lower(),
                                                   "Storage General Purpose gp3 GB Mo")},
        "dataTransferForEC2": {"value": [
            {"entryType": "INBOUND",      "value": in_val,  "unit": in_unit,  "fromRegion": "External" if in_val  else ""},
            {"entryType": "OUTBOUND",     "value": out_val, "unit": out_unit, "toRegion":   "External" if out_val else ""},
            {"entryType": "INTRA_REGION", "value": "",      "unit": "tb_month"},
        ]},
        "workload":                    {"value": {"workloadType": wl_map.get(c.get("workload","constant").lower(),"consistent"), "data": n}},
        "instanceType":                {"value": c.get("instance_type", "t3.micro")},
        "pricingStrategy":             {"value": ps},
        "snapshotFrequency":           {"value": _snapshot(c)[0]},
        "detailedMonitoringCheckbox":  {"value": c.get("detailed_monitoring", False)},
        "ec2AdvancedPricingMetrics":   {"value": int(n)},
    }
    _snap_freq, _snap_amt = _snapshot(c)
    if _snap_freq != "0" and _snap_amt:
        calc["snapshotAmount"] = {"value": _snap_amt, "unit": "gb|NA"}
    if c.get("storage_gb"):
        calc["storageAmount"] = {"value": str(c["storage_gb"]), "unit": "gb|NA"}
    if c.get("storage_type", "gp3").lower() == "gp3":
        calc["gp3Iops"]       = {"value": str(c.get("gp3_iops", 3000))}
        calc["gp3Throughput"] = {"value": str(c.get("gp3_throughput", 125)), "unit": "mbps"}

    return {
        "calculationComponents": calc,
        "serviceCode": "ec2Enhancement",
        "region": rc, "regionName": rn,
        "estimateFor": "template",
        "version": "0.0.68",
        "description": description,
        "serviceName": "Amazon EC2",
    }


# ── S3 ──────────────────────────────────────────────────────────────────────
# Verified: s3StandardStorageSize with gb|month unit

def s3(region="us-east-1", description=None, **c) -> dict:
    """
    storage_gb, put_requests, get_requests, data_returned_gb, data_outbound_gb
    storage_class: standard | intelligent-tiering | standard-ia | one-zone-ia |
                   glacier-instant | glacier-flexible | glacier-deep-archive
    """
    rc, rn = resolve_region(region)
    cls_map = {
        "standard":           "amazonS3Standard",
        "intelligent-tiering":"amazonS3IntelligentTiering",
        "standard-ia":        "amazonS3StandardIA",
        "one-zone-ia":        "amazonS3OneZoneIA",
        "glacier-instant":    "amazonS3GlacierInstantRetrieval",
        "glacier-flexible":   "amazonS3GlacierFlexibleRetrieval",
        "glacier":            "amazonS3GlacierFlexibleRetrieval",
        "glacier-deep-archive":"amazonS3GlacierDeepArchive",
        "deep-archive":       "amazonS3GlacierDeepArchive",
    }
    cls = c.get("storage_class", "standard").lower().replace(" ", "-")
    svc_code = cls_map.get(cls, "amazonS3Standard")

    sub_calc = {"moveToStorageClassMethod": {"value": "No movement required"}}
    if c.get("storage_gb"):
        sub_calc["s3StandardStorageSize"] = {"value": str(c["storage_gb"]), "unit": "gb|month"}
    if c.get("put_requests"):
        sub_calc["s3StandardPutRequests"] = {"value": str(c["put_requests"])}
    if c.get("get_requests"):
        sub_calc["s3StandardGetRequests"] = {"value": str(c["get_requests"])}
    if c.get("data_returned_gb"):
        sub_calc["s3StandardDataReturnedSize"] = {"value": str(c["data_returned_gb"]), "unit": "gb|month"}

    out_val = str(c.get("data_outbound_gb", ""))
    return {
        "serviceCode": "amazonSimpleStorageServiceGroup",
        "region": rc, "regionName": rn,
        "estimateFor": "",
        "version": "0.0.83",
        "description": description,
        "serviceName": "Amazon Simple Storage Service (S3)",
        "subServices": [
            {
                "calculationComponents": sub_calc,
                "serviceCode": svc_code,
                "region": rc,
                "estimateFor": "s3Standard",
                "version": "0.0.71",
                "description": None,
            },
            {
                "calculationComponents": {
                    "dataTransfer": {"value": [
                        {"entryType": "INBOUND",  "value": "",      "unit": "tb_month", "fromRegion": ""},
                        {"entryType": "OUTBOUND", "value": out_val, "unit": "gb_month" if out_val else "tb_month",
                         "toRegion": "External" if out_val else ""},
                    ]}
                },
                "serviceCode": "awsS3DataTransfer",
                "region": rc,
                "estimateFor": "awsS3DataTransfer",
                "version": "0.0.27",
                "description": None,
            },
        ],
    }


# ── Lambda ──────────────────────────────────────────────────────────────────
# Verified: sizeOfMemoryAllocated, durationOfEachRequest, numberOfRequests

def lambda_(region="us-east-1", description=None, **c) -> dict:
    """requests, duration_ms, memory_mb, arch (x86|arm64), free_tier (bool)"""
    rc, rn = resolve_region(region)
    arch = "1" if c.get("arch", "x86").lower() in ("x86", "x86_64") else "2"
    free = "0" if c.get("free_tier", True) else "1"
    calc = {
        "selectArchitectureRequests":                       {"value": arch},
        "selectArchitectureConcurrency":                    {"value": arch},
        "lambdaFunctionIncludeFreeTier_lambdaInvokeMode":   {"value": free},
        "storageAmountEphemeral":                           {"value": str(c.get("ephemeral_mb", 512)), "unit": "mb|NA"},
    }
    if c.get("requests"):
        calc["numberOfRequests"]      = {"value": str(c["requests"]), "unit": "perMonth"}
    if c.get("duration_ms"):
        calc["durationOfEachRequest"] = {"value": str(c["duration_ms"])}
    if c.get("memory_mb"):
        calc["sizeOfMemoryAllocated"] = {"value": str(c["memory_mb"]), "unit": "mb|NA"}

    return {
        "calculationComponents": calc,
        "serviceCode": "aWSLambda",
        "region": rc, "regionName": rn,
        "estimateFor": "lambdaWithFreeTier",
        "version": "0.0.146",
        "description": description,
        "serviceName": "AWS Lambda",
    }


# ── RDS ─────────────────────────────────────────────────────────────────────
# Verified: columnFormIPM with "undefined" utilization key

# Per-engine metadata verified live from calculator.aws (June 2026).
# storage_field differs: MySQL/Oracle/SQLServer use "storageType",
# PostgreSQL/MariaDB use "storageVolume".
_RDS_META = {
    "mysql":      {"code": "amazonRDSMySQLDB",     "name": "Amazon RDS for MySQL",
                   "ef": "mySQLDB",          "ver": "0.0.135", "storage": "storageType",
                   "default_instance": "db.t3.micro"},
    "postgresql": {"code": "amazonRDSPostgreSQLDB","name": "Amazon RDS for PostgreSQL",
                   "ef": "rdsForPostgreSQL",  "ver": "0.0.110", "storage": "storageVolume",
                   "default_instance": "db.t3.micro"},
    "oracle":     {"code": "amazonRdsForOracle",   "name": "Amazon RDS for Oracle",
                   "ef": "rdsForOracle",      "ver": "0.0.88",  "storage": "storageType",
                   "default_instance": "db.t3.medium",
                   "col_extra": {"License Model": {"value": "Bring your own license"},
                                 "Database Edition": {"value": "Enterprise"}}},
    "sqlserver":  {"code": "amazonRDSForSQLServer","name": "Amazon RDS for SQL Server",
                   "ef": "rdsForOracle",      "ver": "0.0.124", "storage": "storageType",
                   "default_instance": "db.t3.medium",
                   "calc_extra": {"optimize": {"value": "0"}},
                   "col_extra": {"License Model": {"value": "License included"},
                                 "Database Edition": {"value": "Standard"},
                                 "Unbundled Licensing": {"value": "FALSE"}}},
    "mariadb":    {"code": "amazonRDSMariaDB",     "name": "Amazon RDS for MariaDB",
                   "ef": "rdsForMariaDB",     "ver": "0.0.132", "storage": "storageVolume",
                   "default_instance": "db.t3.micro"},
}
_RDS_META["postgres"]   = _RDS_META["postgresql"]
_RDS_META["sql-server"] = _RDS_META["sqlserver"]
_RDS_META["sql server"] = _RDS_META["sqlserver"]


def rds(engine="mysql", region="us-east-1", description=None, **c) -> dict:
    """
    engine: mysql|postgresql|oracle|sqlserver|mariadb
    nodes, instance_type, storage_gb, storage_type (gp2|gp3|io1),
    deployment (single-az|multi-az), pricing (on-demand|reserved)
    """
    rc, rn = resolve_region(region)
    m = _RDS_META.get(engine.lower(), _RDS_META["mysql"])
    st_map = {"gp2": "General Purpose", "gp3": "General Purpose (gp3)",
              "io1": "Provisioned IOPS", "io2": "Provisioned IOPS io2", "magnetic": "Magnetic"}
    multi = c.get("deployment", "single-az").lower() in ("multi-az", "multi az", "multiaz")
    term_type = "Reserved_1Year_NoUpfront" if "reserved" in c.get("pricing", "").lower() else "OnDemand"

    col = {
        "Number of Nodes": {"value": str(c.get("nodes", 1))},
        "TermType":        {"value": term_type},
        "Instance Type":   {"value": c.get("instance_type", m["default_instance"])},
        "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
        "Deployment Option": {"value": "Multi-AZ" if multi else "Single-AZ"},
    }
    col.update(m.get("col_extra", {}))

    calc = {
        "createRDSProxy":           {"value": "0"},
        "storageAmount":            {"value": str(c.get("storage_gb", 20)), "unit": "gb|NA"},
        m["storage"]:               {"value": st_map.get(c.get("storage_type","gp2").lower(), "General Purpose")},
        "DatabaseInsightsSelected": {"value": "0"},
        "retentionPeriod":          {"value": "0"},
        "addRDSExtendedSupport":    {"value": "0"},
        "RDSExtendedSupportYear":   {"value": "year12"},
        "columnFormIPM":            {"value": [col]},
    }
    calc.update(m.get("calc_extra", {}))

    return {
        "calculationComponents": calc,
        "serviceCode": m["code"],
        "region": rc, "regionName": rn,
        "estimateFor": m["ef"],
        "version": m["ver"],
        "description": description,
        "serviceName": m["name"],
    }


# ── Aurora ───────────────────────────────────────────────────────────────────
# Verified live from calculator.aws (June 2026):
#   MySQL      -> serviceCode amazonAuroraMySQLCompatible      (new engine, v0.0.167)
#   PostgreSQL -> serviceCode amazonRDSAuroraPostgreSQLCompatibleDB (v0.0.149)

def _instance_family(instance_type: str) -> str:
    """Map a db.<class>.<size> instance type to its Aurora instance family label."""
    cls = instance_type.replace("db.", "").split(".")[0].lower()
    prefix = cls[0]
    if prefix in ("r", "x", "z"):
        return "Memory optimized"
    if prefix == "c":
        return "Compute optimized"
    if prefix == "t":
        return "Burstable Performance"
    return "General purpose"


def aurora(engine="mysql", region="us-east-1", description=None, **c) -> dict:
    """engine: mysql|postgresql, nodes, instance_type, edition, pricing"""
    rc, rn = resolve_region(region)
    pg = "postgres" in engine.lower()
    nodes = str(c.get("nodes", 1))
    itype = c.get("instance_type", "db.r6g.large")
    term  = "Reserved_1Year_NoUpfront" if "reserved" in c.get("pricing", "").lower() else "OnDemand"

    if pg:
        col = {
            "Number of Nodes": {"value": nodes},
            "Instance Type":   {"value": itype},
            "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
            "TermType":        {"value": term},
        }
        calc = {
            "edition":                  {"value": c.get("edition", "auroraStandard")},
            "createRDSProxy":           {"value": "0"},
            "totalReads_BaseIO":        {"value": "1", "unit": "perSecond"},
            "totalWrites_PeakIO":       {"value": "1", "unit": "perSecond"},
            "durationPeakWriteId":      {"value": "1", "unit": "perMonth"},
            "DatabaseInsightsSelected": {"value": "0"},
            "retentionPeriod":          {"value": "0"},
            "addRDSExtendedSupport":    {"value": "0"},
            "RDSExtendedSupportYear":   {"value": "year12"},
            "columnFormIPM":            {"value": [col]},
        }
        if c.get("storage_gb"):
            calc["storageAmount"] = {"value": str(c["storage_gb"]), "unit": "gb|NA"}
        if c.get("backup_gb"):
            calc["additionalBackupStorage"] = {"value": str(c["backup_gb"]), "unit": "gb|NA"}
        return {
            "calculationComponents": calc,
            "serviceCode": "amazonRDSAuroraPostgreSQLCompatibleDB",
            "region": rc, "regionName": rn,
            "estimateFor": "AuroraPostgreSQLCompatibleDB",
            "version": "0.0.149",
            "description": description,
            "serviceName": "Amazon Aurora PostgreSQL-Compatible DB",
        }

    # MySQL — newer calculator engine
    col = {
        "Instance Type":   {"value": itype},
        "Number of Nodes": {"value": nodes},
        "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
        "Instance Family": {"value": _instance_family(itype)},
        "TermType":        {"value": term},
    }
    calc = {
        "edition":                  {"value": c.get("edition", "auroraStandard")},
        "createRDSProxy":           {"value": "0"},
        "changeRecordsPerStatement":{"value": "0.38"},
        "averageStatements":        {"value": "100", "unit": "perSecond"},
        "totalReads_BaseIO":        {"value": "1", "unit": "perSecond"},
        "totalWrites_PeakIO":       {"value": "1", "unit": "perSecond"},
        "durationPeakWriteId":      {"value": "1", "unit": "perMonth"},
        "DatabaseInsightsSelected": {"value": "0"},
        "retentionPeriod":          {"value": "0"},
        "addRDSExtendedSupport":    {"value": "0"},
        "columnFormIPM":            {"value": [col]},
    }
    if c.get("storage_gb"):
        calc["storageAmount"] = {"value": str(c["storage_gb"]), "unit": "gb|NA"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonAuroraMySQLCompatible",
        "region": rc, "regionName": rn,
        "estimateFor": "auroraMySQLCompatible",
        "version": "0.0.167",
        "description": description,
        "serviceName": "Amazon Aurora MySQL-Compatible",
    }


# ── ELB ─────────────────────────────────────────────────────────────────────
# Verified: sub-service structure with exact field names

def elb(region="us-east-1", description=None, **c) -> dict:
    """
    lb_type: alb|nlb|gwlb|classic
    load_balancers, data_processed_gb, connections_per_min, requests_per_sec
    """
    rc, rn = resolve_region(region)
    t = c.get("lb_type", "alb").lower()
    lbs = str(c.get("load_balancers", 1))
    # data processed is entered per hour (gb|hour); accept a monthly figure and convert
    data_hr = str(round(c.get("data_processed_gb", 100) / 730.0, 4))

    if t in ("nlb", "network"):
        sub_code = "networkLoadBalancer"
        sub_calc = {
            "numberOfNetworkLoadBalancers": {"value": lbs},
            "sizeOfDataProcessedForTCPForNLB": {"value": data_hr, "unit": "gb|hour"},
            "averageNumberOfNewTCPConnectionsPerNLB": {"value": str(c.get("connections_per_sec", 100)), "unit": "perSecond"},
            "averageConnectionDurationTCP": {"value": str(c.get("connection_duration_sec", 300)), "unit": "sec"},
        }
    elif t in ("gwlb", "gateway"):
        sub_code = "gatewayLoadBalancer"
        sub_calc = {
            "numberOfGatewayLoadBalancers": {"value": lbs},
            "sizeOfDataProcessedForGLB": {"value": data_hr, "unit": "gb|hour"},
        }
    else:  # ALB (default)
        sub_code = "applicationLoadBalancer"
        sub_calc = {
            "numberOfApplicationLoadBalancers": {"value": lbs},
            "sizeOfDataProcessedForEC2InstanceAndIPAddressTargets": {"value": data_hr, "unit": "gb|hour"},
            "sizeOfBytesProcessedForLambdaFunctionTargets": {"value": "0", "unit": "gb|hour"},
            "averageNumberOfNewConnectionsPerALB":   {"value": str(c.get("connections_per_sec", 100)), "unit": "perSecond"},
            "averageConnectionDuration":             {"value": str(c.get("connection_duration_sec", 300)), "unit": "sec"},
            "averageNumberOfRequestsPerALBPerSecond":{"value": str(c.get("requests_per_sec", 100))},
            "averageNumberOfRuleEvaluationsPerRequest":{"value": str(c.get("rule_evaluations", 1))},
        }

    return {
        "serviceCode": "elasticLoadBalancing",
        "region": rc, "regionName": rn,
        "estimateFor": "elasticLoadBalancingGroups",
        "version": "0.0.28",
        "description": description,
        "serviceName": "Elastic Load Balancing",
        "subServices": [
            {"calculationComponents": sub_calc, "serviceCode": sub_code,
             "region": rc, "estimateFor": "template_0", "version": "0.0.28", "description": None}
        ],
    }


# ── EBS ─────────────────────────────────────────────────────────────────────
# Verified from browser capture

def ebs(region="us-east-1", description=None, **c) -> dict:
    """volumes, storage_type (gp3|gp2|io1|io2|st1|sc1), storage_gb, iops"""
    rc, rn = resolve_region(region)
    st_map = {
        "gp3": "Storage General Purpose gp3 GB Mo",
        "gp2": "Storage General Purpose gp2 GB Mo",
        "io1": "Storage Provisioned IOPS SSD (io1) GB Mo",
        "io2": "Storage Provisioned IOPS SSD (io2) GB Mo",
        "st1": "Storage Throughput Optimized HDD (st1) GB Mo",
        "sc1": "Storage Cold HDD (sc1) GB Mo",
    }
    _snap_freq, _snap_amt = _snapshot(c)
    calc = {
        "numberOfInstances":    {"value": str(c.get("volumes", 1))},
        "durationOfInstanceRuns":{"value": "730", "unit": "hours"},
        "storageType":          {"value": st_map.get(c.get("storage_type","gp3").lower(), "Storage General Purpose GB Mo")},
        "storageAmount":        {"value": str(c.get("storage_gb", 30)), "unit": "gb|NA"},
        "snapshotFrequency":    {"value": _snap_freq},
        "snapshotAmount":       {"value": _snap_amt or "0", "unit": "gb|NA"},
    }
    if c.get("iops") and "io" in c.get("storage_type","gp3"):
        calc["iopsAmount"] = {"value": str(c["iops"])}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonElasticBlockStore",
        "region": rc, "regionName": rn,
        "estimateFor": "elasticBlockStore",
        "version": "0.0.159",
        "description": description,
        "serviceName": "Amazon Elastic Block Store (EBS)",
    }


# ── EFS ─────────────────────────────────────────────────────────────────────

def efs(region="us-east-1", description=None, **c) -> dict:
    """storage_gb, read_gb, write_gb (elastic throughput data)"""
    rc, rn = resolve_region(region)
    calc = {}
    if c.get("storage_gb"):
        calc["standardStorageSize"] = {"value": str(c["storage_gb"]), "unit": "gb|NA"}
    if c.get("read_gb"):
        calc["elasticThroughputReadDataInputSS"] = {"value": str(c["read_gb"]), "unit": "gb|month"}
    if c.get("write_gb"):
        calc["elasticThroughputWriteDataInputSS"] = {"value": str(c["write_gb"]), "unit": "gb|month"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonEFS",
        "region": rc, "regionName": rn,
        "estimateFor": "elasticFileSystem",
        "version": "0.0.76",
        "description": description,
        "serviceName": "Amazon Elastic File System (EFS)",
    }


# ── EKS ─────────────────────────────────────────────────────────────────────
# Verified from real browser capture

def eks(region="us-east-1", description=None, **c) -> dict:
    """clusters, hybrid_nodes"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "numberOfEKSClusters": {"value": str(c.get("clusters", 1))},
            "numberOfHybridNodes": {"value": str(c.get("hybrid_nodes", 0)), "unit": "perMonth"},
        },
        "serviceCode": "awsEks",
        "region": rc, "regionName": rn,
        "estimateFor": "Amazon EKS",
        "version": "0.0.40",
        "description": description,
        "serviceName": "Amazon EKS",
    }


# ── CloudFront ───────────────────────────────────────────────────────────────
# Verified: pay-as-you-go uses these exact field labels

def cloudfront(region="us-east-1", description=None, **c) -> dict:
    """
    data_transfer_gb (out to internet), origin_transfer_gb, https_requests
    Pay-as-you-go pricing.
    """
    rc, rn = resolve_region(region)
    calc = {}
    if c.get("data_transfer_gb"):
        calc["dataTransferedToInternet_US"] = {"value": str(c["data_transfer_gb"]), "unit": "gb|month"}
    if c.get("origin_transfer_gb"):
        calc["dataTransferedToOrigin_US"] = {"value": str(c["origin_transfer_gb"]), "unit": "gb|month"}
    if c.get("https_requests"):
        calc["numberOfHttpsRequests_US"] = {"value": str(c["https_requests"]), "unit": "perMonth"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonCloudFront",
        "region": rc, "regionName": rn,
        "estimateFor": "CDN",
        "version": "0.0.47",
        "description": description,
        "serviceName": "Amazon CloudFront",
    }


# ── CloudWatch ───────────────────────────────────────────────────────────────
# Verified from real estimate

def cloudwatch(region="us-east-1", description=None, **c) -> dict:
    """metrics, logs_gb, dashboards, log_insights_gb, mobile_events"""
    rc, rn = resolve_region(region)
    calc = {}
    if c.get("metrics"):
        calc["totalNumberOfMetrics"] = {"value": str(c["metrics"])}
    if c.get("logs_gb"):
        calc["sizeOfStandardLogsDataIngested"] = {"value": str(c["logs_gb"]), "unit": "gb|NA"}
    if c.get("log_insights_gb"):
        calc["sizeOfLogsInsightsQueriesDataScanned"] = {"value": str(c["log_insights_gb"]), "unit": "gb|NA"}
    if c.get("dashboards"):
        calc["numberOfDashboards"] = {"value": str(c["dashboards"])}
    if c.get("alarms"):
        calc["numberOfAlarmMetrics"] = {"value": str(c["alarms"])}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonCloudWatch",
        "region": rc, "regionName": rn,
        "estimateFor": "CloudWatch",
        "version": "0.0.141",
        "description": description,
        "serviceName": "Amazon CloudWatch",
    }


# ── VPC ──────────────────────────────────────────────────────────────────────
# VPC is a selector that holds networking sub-services. Sub fields verified live
# (June 2026). Supports: Site-to-Site VPN, NAT Gateway, Public IPv4, PrivateLink,
# Transit Gateway. Build a focused estimate by passing the relevant config keys.

def vpc(region="us-east-1", description=None, **c) -> dict:
    """
    Site-to-Site VPN:  vpn_connections, vpn_duration_hrs
    NAT Gateway:       nat_gateways, nat_data_gb
    Public IPv4:       public_ips, idle_ips
    PrivateLink:       vpc_endpoints, endpoint_azs, endpoint_data_gb
    Transit Gateway:   tgw_attachments, tgw_data_gb
    """
    rc, rn = resolve_region(region)
    subs = []

    if c.get("vpn_connections"):
        subs.append({
            "calculationComponents": {
                "numberOfSiteToSiteVPNConnections": {"value": str(c["vpn_connections"])},
                "averageDurationForEachConnection": {"value": str(c.get("vpn_duration_hrs", 24)), "unit": "perDay"},
                "vpnConnection_numberOfWorkDays":   {"value": str(c.get("vpn_work_days", 22))},
            },
            "serviceCode": "vpnConnectionVpc",
            "region": rc, "estimateFor": "VPNConnection", "version": "0.0.19", "description": None,
        })

    if c.get("nat_gateways"):
        # Bill by the "regional" model only (count x AZ = total NAT gateways).
        # Setting the per-gateway fields too would double-count.
        subs.append({
            "calculationComponents": {
                "regionalNatGatewayCount":        {"value": "1"},
                "regionalNatGatewayAzCount":      {"value": str(c.get("nat_azs", c["nat_gateways"]))},
                "regionalNatGatewayDataProcessed":{"value": str(c.get("nat_data_gb", 0)), "unit": "gb|month"},
            },
            "serviceCode": "networkAddressTranslationNatGatewayVpc",
            "region": rc, "estimateFor": "networkAddressTranslationGateway", "version": "0.0.19", "description": None,
        })

    if c.get("public_ips") or c.get("idle_ips"):
        subs.append({
            "calculationComponents": {
                "numberOfInusepublicipv4address":  {"value": str(c.get("public_ips", 1))},
                "numberOfIdlepublicipv4address":   {"value": str(c.get("idle_ips", 0))},
            },
            "serviceCode": "publicIpv4Address",
            "region": rc, "estimateFor": "ipv4publicaddress", "version": "0.0.17", "description": None,
        })

    if c.get("vpc_endpoints"):
        subs.append({
            "calculationComponents": {
                "numberOfInterfaceVPCEndpointsPerRegion":     {"value": str(c["vpc_endpoints"])},
                "numberOfAvailabilityZonesEndpointsDeployed": {"value": str(c.get("endpoint_azs", 2))},
                "dataProcessedByEachVPCENIAZ":                {"value": str(c.get("endpoint_data_gb", 0)), "unit": "gb|month"},
            },
            "serviceCode": "awsPrivateLinkVpc",
            "region": rc, "estimateFor": "awsPrivateLink", "version": "0.0.17", "description": None,
        })

    if c.get("tgw_attachments"):
        subs.append({
            "calculationComponents": {
                "numberOfTransitGatewayAttachments":   {"value": str(c["tgw_attachments"])},
                "dataProcessedPerTransitGateway":      {"value": str(c.get("tgw_data_gb", 0)), "unit": "gb|month"},
            },
            "serviceCode": "transitGatewayVpc",
            "region": rc, "estimateFor": "transitGateway", "version": "0.0.19", "description": None,
        })

    return {
        "serviceCode": "amazonVirtualPrivateCloud",
        "region": rc, "regionName": rn,
        "estimateFor": "virtualPrivateCloudSubServiceSelector",
        "version": "0.0.101",
        "description": description,
        "serviceName": "Amazon Virtual Private Cloud (VPC)",
        "subServices": subs,
    }


# Standalone wrappers so users can request a single networking item directly.
def site_to_site_vpn(region="us-east-1", description=None, **c) -> dict:
    """connections (vpn_connections), vpn_duration_hrs"""
    c.setdefault("vpn_connections", c.pop("connections", 1))
    return vpc(region, description, **c)


def nat_gateway(region="us-east-1", description=None, **c) -> dict:
    """nat_gateways (or gateways), nat_data_gb"""
    if "gateways" in c:
        c["nat_gateways"] = c.pop("gateways")
    c.setdefault("nat_gateways", 1)
    return vpc(region, description, **c)


def transit_gateway(region="us-east-1", description=None, **c) -> dict:
    """tgw_attachments (or attachments), tgw_data_gb"""
    if "attachments" in c:
        c["tgw_attachments"] = c.pop("attachments")
    c.setdefault("tgw_attachments", 1)
    return vpc(region, description, **c)


def privatelink(region="us-east-1", description=None, **c) -> dict:
    """vpc_endpoints (or endpoints), endpoint_data_gb"""
    if "endpoints" in c:
        c["vpc_endpoints"] = c.pop("endpoints")
    c.setdefault("vpc_endpoints", 1)
    return vpc(region, description, **c)


# ── WAF ──────────────────────────────────────────────────────────────────────
# Verified from real estimate

# ── Network Firewall ───────────────────────────────────────────────────────────

def network_firewall(region="us-east-1", description=None, **c) -> dict:
    """endpoints, secondary_endpoints, data_processed_gb, advanced_inspection (bool)"""
    rc, rn = resolve_region(region)
    endpoints = c.get("endpoints", 1)
    calc = {
        "networkfirewallendpoints": {"value": str(endpoints)},
        "usage":                    {"value": "730", "unit": "hr"},
    }
    if c.get("secondary_endpoints"):
        calc["Number_of_Network_Firewall_secondary_endpoints"] = {"value": str(c["secondary_endpoints"])}
        calc["Usage_per_secondary_endpoint"] = {"value": "730", "unit": "hr"}
    if c.get("advanced_inspection"):
        calc["advanceInspection"] = {"value": "730", "unit": "hr"}
    if c.get("data_processed_gb"):
        calc["dataProcessed"] = {"value": str(c["data_processed_gb"]), "unit": "gb|NA"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonNetworkFirewall",
        "region": rc, "regionName": rn,
        "estimateFor": "AWSnetworkfirewall",
        "version": "0.0.37",
        "description": description,
        "serviceName": "AWS Network Firewall",
    }


# ── AWS Backup (best-effort) ───────────────────────────────────────────────────
# NOTE: AWS Backup's calculator form nests the "primary data amount" + retention
# inside an accordion that does not serialise via the save API, so the baked cost
# may show $0 — set the backup storage on the AWS page after opening the link.

def aws_backup(region="us-east-1", description=None, **c) -> dict:
    """daily_change_pct, annual_growth_pct (EFS-style backup model; best-effort)"""
    rc, rn = resolve_region(region)
    sub = {
        "calculationComponents": {
            "dailyChangeOfPrimaryUsage":  {"value": str(c.get("daily_change_pct", 5))},
            "annualGrowthOfPrimaryUsage": {"value": str(c.get("annual_growth_pct", 10))},
        },
        "serviceCode": "amazonEfsBackup", "region": rc,
        "estimateFor": "efsBackup", "version": "0.0.44", "description": None,
    }
    return {
        "serviceCode": "awsBackup",
        "region": rc, "regionName": rn,
        "estimateFor": "awsBackupSelector",
        "version": "0.0.101",
        "description": description,
        "serviceName": "AWS Backup",
        "subServices": [sub],
    }


# ── Elastic Disaster Recovery (EDR / AWS DRS) ──────────────────────────────────

def disaster_recovery(region="us-east-1", description=None, **c) -> dict:
    """source_servers, disks, storage_gb, change_rate_pct, retention_days, percent_large_disks"""
    rc, rn = resolve_region(region)
    sub_calc = {
        "numberOnPremiseServerReplicated": {"value": str(c.get("source_servers", 1))},
        "numberOfDisk":                    {"value": str(c.get("disks", 2))},
        "avgChangeRateOfDisk":             {"value": str(c.get("change_rate_pct", 5))},
        "storageAmount":                   {"value": str(c.get("storage_gb", 100)), "unit": "gb|NA"},
        "numberOfRetentionDays":           {"value": str(c.get("retention_days", 7))},
        "ebsVolumeCostType":               {"value": "avg"},
        "percentOfHigherPerformance":      {"value": str(c.get("percent_large_disks", 0))},
    }
    return {
        "serviceCode": "awsElasticDisasterRecovery",
        "region": rc, "regionName": rn,
        "estimateFor": "awsDRSGroups",
        "version": "0.0.17",
        "description": description,
        "serviceName": "AWS Elastic Disaster Recovery",
        "subServices": [
            {"calculationComponents": sub_calc, "serviceCode": "awsDrsRecoveryReplication",
             "region": rc, "estimateFor": "template1", "version": "0.0.37", "description": None}
        ],
    }


def waf(region="us-east-1", description=None, **c) -> dict:
    """web_acls, rules_per_acl, requests_millions"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "numberOfWebAcls":       {"value": str(c.get("web_acls", 1)),         "unit": "perMonth"},
            "numberOfRulesPerWebAcl":{"value": str(c.get("rules_per_acl", 10)),   "unit": "perMonth"},
            "numberOfWebRequests":   {"value": str(c.get("requests_millions", 1)), "unit": "perMonth"},
        },
        "serviceCode": "awsWebApplicationFirewall",
        "region": rc, "regionName": rn,
        "estimateFor": "awsWaf",
        "version": "0.0.34",
        "description": description,
        "serviceName": "AWS Web Application Firewall (WAF)",
    }


# ── GuardDuty ────────────────────────────────────────────────────────────────
# Verified from real estimate

def guardduty(region="us-east-1", description=None, **c) -> dict:
    """s3_data_gb, management_events_million, s3_events, ec2_instances, ecs_instances"""
    rc, rn = resolve_region(region)
    calc = {
        "s3Data":                    {"value": str(c.get("s3_data_gb", 10)),             "unit": "gb|month"},
        "managementEventsAnalysis":  {"value": str(c.get("management_events_million", 1)), "unit": "millionPerMonth"},
        "s3Events":                  {"value": str(c.get("s3_events", 1000000)),          "unit": "perMonth"},
        "dnsLogs_EC2":               {"value": str(c.get("dns_logs_gb", 0)),             "unit": "gb|month"},
        "malwareDataScan":           {"value": str(c.get("malware_scan_gb", 0)),         "unit": "gb|month"},
        "vpcFlowLogs_lambda":        {"value": str(c.get("vpc_flow_logs_gb", 0)),        "unit": "gb|month"},
        "s3put":                     {"value": str(c.get("s3_put_events", 10000)),        "unit": "perMonth"},
        "vCPURDS":                   {"value": str(c.get("rds_vcpus", 0)),               "unit": "perMonth"},
        "eksInstances":              {"value": str(c.get("eks_instances", 0)),           "unit": "perMonth"},
        "ecsInstances":              {"value": str(c.get("ecs_instances", 0)),           "unit": "perMonth"},
    }
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonGuardDuty",
        "region": rc, "regionName": rn,
        "estimateFor": "template_0",
        "version": "0.0.75",
        "description": description,
        "serviceName": "Amazon GuardDuty",
    }


# ── Inspector ────────────────────────────────────────────────────────────────
# Verified from real estimate

def inspector(region="us-east-1", description=None, **c) -> dict:
    """ec2_instances, lambda_functions, container_images"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "NumberOfEC2Instance":         {"value": str(c.get("ec2_instances", 0))},
            "numberOfNewImages_continual": {"value": str(c.get("container_images", 10))},
            "avgNoOfLambda":               {"value": str(c.get("lambda_functions", 5))},
            "numberOfNewImages":           {"value": str(c.get("new_images_pushed", 5))},
        },
        "serviceCode": "amazonInspector",
        "region": rc, "regionName": rn,
        "estimateFor": "Inspectorv2",
        "version": "0.0.22",
        "description": description,
        "serviceName": "Amazon Inspector",
    }


# ── Security Hub ─────────────────────────────────────────────────────────────
# Verified from real estimate

def security_hub(region="us-east-1", description=None, **c) -> dict:
    """accounts, security_checks, findings_ingested, automation_rules"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "noOfAccounts":       {"value": str(c.get("accounts", 1))},
            "noOfSecurityChecks": {"value": str(c.get("security_checks", 3000))},
            "noOfIngestion":      {"value": str(c.get("findings_ingested", 10000))},
            "noOfautomationrules":{"value": str(c.get("automation_rules", 10))},
            "noOfcriteria":       {"value": str(c.get("criteria", 10))},
        },
        "serviceCode": "awsSecurityHub",
        "region": rc, "regionName": rn,
        "estimateFor": "template_securityhub",
        "version": "0.0.51",
        "description": description,
        "serviceName": "AWS Security Hub",
    }


# ── KMS ──────────────────────────────────────────────────────────────────────
# Verified from real estimate

def kms(region="us-east-1", description=None, **c) -> dict:
    """keys, symmetric_requests, asymmetric_requests"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "numberOfCmk":              {"value": str(c.get("keys", 1))},
            "numberOfSymmetricRequests":{"value": str(c.get("symmetric_requests", 10000))},
        },
        "serviceCode": "awsKeyManagementService",
        "region": rc, "regionName": rn,
        "estimateFor": "kms",
        "version": "0.0.20",
        "description": description,
        "serviceName": "AWS Key Management Service",
    }


# ── CloudTrail ────────────────────────────────────────────────────────────────
# Verified from real estimate

def cloudtrail(region="us-east-1", description=None, **c) -> dict:
    """write_events_million, read_events_million, s3_events_million, lambda_events_million, data_ingested_gb"""
    rc, rn = resolve_region(region)
    calc = {
        "OpsMult":                       {"value": "1000000"},
        "numberOfWriteTrails":           {"value": str(c.get("write_trails", 1))},
        "numberOfReadTrails":            {"value": str(c.get("read_trails", 1))},
        "dataOpsMult":                   {"value": "1000000"},
        "numberOfS3Trails":              {"value": str(c.get("s3_trails", 1))},
        "numberOfLambdaTrails":          {"value": str(c.get("lambda_trails", 1))},
        "networkActivityOpsMult":        {"value": "1000000"},
        "numberOfNetworkActivityTrails": {"value": "0"},
        "eventMult":                     {"value": "1000000"},
        "numberOfInsightTrails":         {"value": str(c.get("insight_trails", 0))},
    }
    # event counts are entered in millions
    wm = c.get("write_events_million", c.get("events_million"))
    if wm:
        calc["numberOfWriteEvents"] = {"value": str(wm), "unit": "perMonth"}
    if c.get("read_events_million"):
        calc["numberOfReadEvents"] = {"value": str(c["read_events_million"]), "unit": "perMonth"}
    if c.get("s3_events_million"):
        calc["numberOfS3Ops"] = {"value": str(c["s3_events_million"]), "unit": "perMonth"}
    if c.get("lambda_events_million"):
        calc["numberOfLambdaOps"] = {"value": str(c["lambda_events_million"]), "unit": "perMonth"}
    if c.get("data_ingested_gb"):
        calc["dataIngestedCloudtrail"] = {"value": str(c["data_ingested_gb"]), "unit": "gb|NA"}
    return {
        "calculationComponents": calc,
        "serviceCode": "awsCloudTrail",
        "region": rc, "regionName": rn,
        "estimateFor": "template",
        "version": "0.0.46",
        "description": description,
        "serviceName": "AWS CloudTrail",
    }


# ── Config ───────────────────────────────────────────────────────────────────
# Verified from real estimate

def config(region="us-east-1", description=None, **c) -> dict:
    """config_items, rule_evaluations, conformance_evaluations"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "numberOfConfigrationItemsRecorded": {"value": str(c.get("config_items", 1000))},
            "numberOfAWSConfigRuleEvaluations":   {"value": str(c.get("rule_evaluations", 10000))},
            "numberOfConformancePackEvaluations": {"value": str(c.get("conformance_evaluations", 0))},
        },
        "serviceCode": "awsConfig",
        "region": rc, "regionName": rn,
        "estimateFor": "awsConfig",
        "version": "0.0.35",
        "description": description,
        "serviceName": "AWS Config",
    }


# ── Fargate ──────────────────────────────────────────────────────────────────
# Verified from real estimate

def fargate(region="us-east-1", description=None, **c) -> dict:
    """tasks, vcpu, memory_gb, storage_gb, arch (x86|arm64), os (linux|windows)"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "operatingSystem":                 {"value": c.get("os", "linux").lower()},
            "selectArchitecture":              {"value": "arm64" if c.get("arch","").lower()=="arm64" else "x86"},
            "taskDuration":                    {"value": "730", "unit": "hr"},
            "vcpuPerTask":                     {"value": str(c.get("vcpu", 1))},
            "numberOfTasks":                   {"value": str(c.get("tasks", 1)), "unit": "perMonth"},
            "memoryStandardFargateOnDemand":   {"value": str(c.get("memory_gb", 2)), "unit": "gb|NA"},
            "storageAmountECS":                {"value": str(c.get("storage_gb", 20)), "unit": "gb|NA"},
        },
        "serviceCode": "awsFargate",
        "region": rc, "regionName": rn,
        "estimateFor": "template",
        "version": "0.0.66",
        "description": description,
        "serviceName": "AWS Fargate",
    }


# ── ECR ──────────────────────────────────────────────────────────────────────
# Verified from real estimate

def ecr(region="us-east-1", description=None, **c) -> dict:
    """storage_gb, data_inbound_gb, data_outbound_gb"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "amountofdatastored": {"value": str(c.get("storage_gb", 10)), "unit": "gb|month"},
            "dataTransfer": {"value": [
                {"entryType": "INBOUND",  "value": str(c.get("data_inbound_gb",0)), "unit": "gb_month", "fromRegion": "External"},
                {"entryType": "OUTBOUND", "value": str(c.get("data_outbound_gb",0)), "unit": "gb_month", "toRegion": "other"},
            ]},
        },
        "serviceCode": "amazonElasticContainerRegistry",
        "region": rc, "regionName": rn,
        "estimateFor": "template_0",
        "version": "0.0.33",
        "description": description,
        "serviceName": "Amazon Elastic Container Registry",
    }


# ── CodePipeline ─────────────────────────────────────────────────────────────
# Verified from real estimate

def codepipeline(region="us-east-1", description=None, **c) -> dict:
    """pipelines_v1, pipelines_v2"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "numberOfPipelines":    {"value": str(c.get("pipelines_v1", 0))},
            "numberOfPipelines_v2": {"value": str(c.get("pipelines_v2", 1))},
        },
        "serviceCode": "awsCodePipeline",
        "region": rc, "regionName": rn,
        "estimateFor": "awscodepipeline",
        "version": "0.0.18",
        "description": description,
        "serviceName": "AWS CodePipeline",
    }


# ── CodeBuild ────────────────────────────────────────────────────────────────
# Verified from real estimate

def codebuild(region="us-east-1", description=None, **c) -> dict:
    """builds_per_month, avg_build_min, compute_type (general1.small|general1.medium|general1.large)"""
    rc, rn = resolve_region(region)
    return {
        "calculationComponents": {
            "computeType":    {"value": "ondemandec2"},
            "buildsinaMonth": {"value": str(c.get("builds_per_month", 100))},
            "AvgBuildTime":   {"value": str(c.get("avg_build_min", 5)), "unit": "min"},
            "columnFormIPM":  {"value": [{"Compute Type": {"value": c.get("compute_type","general1.small")},
                                          "Operating System": {"value": c.get("os","Linux")}}]},
        },
        "serviceCode": "awsCodeBuild",
        "region": rc, "regionName": rn,
        "estimateFor": "template_0",
        "version": "0.0.44",
        "description": description,
        "serviceName": "AWS CodeBuild",
    }


# ── DynamoDB ─────────────────────────────────────────────────────────────────
# Verified: uses sub-service structure

def dynamodb(region="us-east-1", description=None, **c) -> dict:
    """
    mode: provisioned (default) | on-demand
    read_capacity, write_capacity, storage_gb, table_class (standard|standard-ia)
    OR for on-demand: read_request_units, write_request_units
    """
    rc, rn = resolve_region(region)
    mode = c.get("mode", "provisioned").lower()

    if "on-demand" in mode or "ondemand" in mode:
        sub_code = "amazonDynamoDbOnDemandCapacity"
        sub_calc = {
            "selectTableClassOnDemand": {"value": c.get("table_class","standard").lower().replace("-","_")},
            "averageItemSizeForAllAttributesOnDemand": {"value": str(c.get("item_size_kb", 1)), "unit": "kb|NA"},
            "readRequestUnits":  {"value": str(c.get("read_request_units", 1000000))},
            "writeRequestUnits": {"value": str(c.get("write_request_units", 1000000))},
        }
    else:
        sub_code = "amazonDynamoDbProvisionedThroughputCapacity"
        sub_calc = {
            "selectTableClassProvisioned": {"value": c.get("table_class","standard")},
            "averageItemSizeForAllAttributesProvisioned": {"value": str(c.get("item_size_kb", 1)), "unit": "kb|NA"},
            "standardWritesId":        {"value": str(c.get("write_capacity", 5))},
            "transactionalWriteId":    {"value": "0"},
            "eventuallyConsistentId":  {"value": str(c.get("read_capacity", 5))},
            "stronglyConsistentId":    {"value": "0"},
            "transactionalId":         {"value": "0"},
            "baselineWriteRateId":     {"value": str(c.get("write_capacity", 5)), "unit": "perSecond"},
            "peakWriteRateId":         {"value": str(c.get("write_capacity", 5) * 4), "unit": "perSecond"},
            "durationPeakWriteId":     {"value": "72", "unit": "hoursPerMonth"},
            "percentWriteReservedCapacity": {"value": "100"},
            "reservedCapacityTermWrite":    {"value": "1yr"},
            "baselineReadRateId":      {"value": str(c.get("read_capacity", 5)), "unit": "perSecond"},
            "peakReadRateId":          {"value": str(c.get("read_capacity", 5) * 4), "unit": "perSecond"},
            "durationPeakReadId":      {"value": "72", "unit": "hoursPerMonth"},
            "percentReservedCapacity": {"value": "100"},
            "reservedCapacityTermRead":{"value": "1yr"},
        }
    if c.get("storage_gb"):
        sub_calc["dataStorageSize"] = {"value": str(c["storage_gb"]), "unit": "gb|month"}

    return {
        "serviceCode": "amazonDynamoDb",
        "region": rc, "regionName": rn,
        "estimateFor": "simpleStorageServiceClassesGroup",
        "version": "0.0.65",
        "description": description,
        "serviceName": "Amazon DynamoDB",
        "subServices": [
            {"calculationComponents": sub_calc, "serviceCode": sub_code,
             "region": rc, "estimateFor": "dynamoDBProvisioned" if "provision" in mode else "dynamoDBOnDemand",
             "version": "0.0.192", "description": None}
        ],
    }


# ── API Gateway ───────────────────────────────────────────────────────────────

def api_gateway(region="us-east-1", description=None, **c) -> dict:
    """http_requests_million, rest_requests_million, avg_size_kb
    Request counts are entered in MILLIONS (APIOpsMult/RESTMult are the x1e6 multipliers)."""
    rc, rn = resolve_region(region)
    calc = {
        "APIOpsMult":    {"value": "1000000"},
        "dataPerRequest":{"value": str(c.get("avg_size_kb", 34)), "unit": "kb|NA"},
        "RESTMult":      {"value": "1000000"},
        "cacheSize":     {"value": "[ZERO_COST]"},
        "WebSocketMult": {"value": "1000"},
        "msgSize":       {"value": "32", "unit": "kb|NA"},
    }
    if c.get("http_requests_million"):
        calc["numberOfAPIRequests"] = {"value": str(c["http_requests_million"]), "unit": "perMonth"}
    if c.get("rest_requests_million"):
        calc["numberOfRESTRequests"] = {"value": str(c["rest_requests_million"]), "unit": "perMonth"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonApiGateway",
        "region": rc, "regionName": rn,
        "estimateFor": "template",
        "version": "0.0.59",
        "description": description,
        "serviceName": "Amazon API Gateway",
    }


# ── Route 53 ──────────────────────────────────────────────────────────────────

def route53(region="us-east-1", description=None, **c) -> dict:
    """hosted_zones, records, queries_million, health_checks"""
    rc, rn = resolve_region(region)
    calc = {}
    if c.get("hosted_zones"):
        calc["numberOfHostedZones"] = {"value": str(c["hosted_zones"])}
    if c.get("records"):
        calc["RRsetRecord"] = {"value": str(c["records"])}
    if c.get("queries_million"):
        calc["numberOfStandardQueries"] = {"value": str(c["queries_million"]), "unit": "millionPerMonth"}
    if c.get("health_checks"):
        calc["numberOfBasicChecksWithinAWS"] = {"value": str(c["health_checks"])}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonRoute53",
        "region": rc, "regionName": rn,
        "estimateFor": "Route53",
        "version": "0.0.88",
        "description": description,
        "serviceName": "Amazon Route 53",
    }


# ── SQS ───────────────────────────────────────────────────────────────────────

def sqs(region="us-east-1", description=None, **c) -> dict:
    """requests_million, fifo (bool)"""
    rc, rn = resolve_region(region)
    field = "fifoQueueRequests" if c.get("fifo") else "standardQueueRequests"
    calc = {}
    if c.get("requests_million"):
        # field expects the count in millions
        calc[field] = {"value": str(c["requests_million"]), "unit": "perMonth"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonSimpleQueueService",
        "region": rc, "regionName": rn,
        "estimateFor": "simpleQueueService",
        "version": "0.0.47",
        "description": description,
        "serviceName": "Amazon Simple Queue Service (SQS)",
    }


# ── SNS ───────────────────────────────────────────────────────────────────────

def sns(region="us-east-1", description=None, **c) -> dict:
    """notifications_million (publish requests), http_million, email_million, sqs_million, lambda_million"""
    rc, rn = resolve_region(region)
    sub_calc = {}
    if c.get("notifications_million"):
        sub_calc["numberOfRequests"] = {"value": str(c["notifications_million"]), "unit": "millionPerMonth"}
    if c.get("http_million"):
        sub_calc["numberOfHTTPNotifications"] = {"value": str(c["http_million"]), "unit": "millionPerMonth"}
    if c.get("email_million"):
        sub_calc["numberOfEmailNotifications"] = {"value": str(c["email_million"]), "unit": "millionPerMonth"}
    if c.get("sqs_million"):
        sub_calc["numberOfSQSNotifications"] = {"value": str(c["sqs_million"]), "unit": "millionPerMonth"}
    if c.get("lambda_million"):
        sub_calc["aws_Lambda"] = {"value": str(c["lambda_million"]), "unit": "millionPerMonth"}
    return {
        "serviceCode": "amazonSimpleNotificationService",
        "region": rc, "regionName": rn,
        "estimateFor": "amazonSnsClassesGroup",
        "version": "0.0.24",
        "description": description,
        "serviceName": "Amazon Simple Notification Service (SNS)",
        "subServices": [
            {"calculationComponents": sub_calc, "serviceCode": "standardTopics",
             "region": rc, "estimateFor": "sns_t1", "version": "0.0.64", "description": None}
        ],
    }


# ── SES ───────────────────────────────────────────────────────────────────────

def ses(region="us-east-1", description=None, **c) -> dict:
    """emails_sent_thousand, emails_received_thousand (converted to per-month counts)"""
    rc, rn = resolve_region(region)
    calc = {"virtualDeliveryManagerOption": {"value": "0"}}
    if c.get("emails_sent_thousand"):
        calc["numberOfEmailMessagesSentFromEC2"] = {
            "value": str(int(c["emails_sent_thousand"] * 1000)), "unit": "perMonth"}
    if c.get("emails_received_thousand"):
        calc["numberOfEmailMessagesReceived"] = {
            "value": str(int(c["emails_received_thousand"] * 1000)), "unit": "perMonth"}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonSimpleEmailService",
        "region": rc, "regionName": rn,
        "estimateFor": "simpleEmailService",
        "version": "0.0.52",
        "description": description,
        "serviceName": "Amazon Simple Email Service (SES)",
    }


# ── Cognito ───────────────────────────────────────────────────────────────────

def cognito(region="us-east-1", description=None, **c) -> dict:
    """maus, token_requests, app_clients, saml_percent, advanced_security"""
    rc, rn = resolve_region(region)
    calc = {
        "cognito_advSecurityFeatures": {"value": "1" if c.get("advanced_security") else "0"},
    }
    if c.get("maus"):
        calc["cognito_NumberOfMAUs"] = {"value": str(c["maus"])}
    if c.get("token_requests"):
        calc["cognito_NumberOfTokenRequests"] = {"value": str(c["token_requests"])}
    if c.get("app_clients"):
        calc["cognito_NumberOfAppClients"] = {"value": str(c["app_clients"])}
    if c.get("saml_percent"):
        calc["percentSAMLOIDC"] = {"value": str(c["saml_percent"])}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonCognito",
        "region": rc, "regionName": rn,
        "estimateFor": "Cognito",
        "version": "0.0.65",
        "description": description,
        "serviceName": "Amazon Cognito",
    }


# ── OpenSearch ────────────────────────────────────────────────────────────────

def opensearch(region="us-east-1", description=None, **c) -> dict:
    """nodes, instance_type (e.g. r5.large.search), master_nodes (0|3|5), pricing"""
    rc, rn = resolve_region(region)
    nodes = str(c.get("nodes", 1))
    itype = c.get("instance_type", "r5.large.search")
    fam = _instance_family(itype.split(".search")[0])
    term = "Reserved_1Year_NoUpfront" if "reserved" in c.get("pricing", "").lower() else "OnDemand"
    data_col = {
        "Number of Nodes Data instance": {"value": nodes},
        "Instance Type":   {"value": itype},
        "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
        "Instance Family": {"value": fam},
        "TermType":        {"value": term},
        "Storage":         {"value": "EBS Only"},
    }
    calc = {
        "numberOfInstances": {"value": nodes},
        "storageType":       {"value": "GP3"},
        "columnFormIPM_1":   {"value": [data_col]},
    }
    master = c.get("master_nodes", 0)
    if master:
        calc["columnFormIPM_2"] = {"value": [{
            "Number of Nodes Dedicated master": {"value": str(master)},
            "Instance Type":   {"value": itype},
            "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
            "Instance Family": {"value": fam},
            "TermType":        {"value": term},
            "Storage":         {"value": "EBS Only"},
        }]}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonElasticsearchService",
        "region": rc, "regionName": rn,
        "estimateFor": "elasticSearchService",
        "version": "0.0.167",
        "description": description,
        "serviceName": "Amazon OpenSearch Service",
    }


# ── Kinesis ───────────────────────────────────────────────────────────────────

def kinesis(region="us-east-1", description=None, **c) -> dict:
    """records_per_second, record_size_kb, retention_days, consumers, fanout_consumers (on-demand mode)"""
    rc, rn = resolve_region(region)
    calc = {
        "numberOfRetentionDaysOnDemand": {"value": str(c.get("retention_days", 1)), "unit": "day"},
    }
    if c.get("records_per_second"):
        calc["numberOfRecordsOnDemand"] = {"value": str(c["records_per_second"]), "unit": "perSecond"}
    if c.get("record_size_kb"):
        calc["averageRecordSizeOnDemand"] = {"value": str(c["record_size_kb"]), "unit": "kb|NA"}
    if c.get("consumers"):
        calc["numberOfConsumerApplicationsOnDemand"] = {"value": str(c["consumers"])}
    if c.get("fanout_consumers"):
        calc["numberOfEnhancedFanoutConsumersOnDemand"] = {"value": str(c["fanout_consumers"])}
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonKinesisDataStreams",
        "region": rc, "regionName": rn,
        "estimateFor": "amazonKinesisDataStreamsOnDemand",
        "version": "0.0.95",
        "description": description,
        "serviceName": "Amazon Kinesis Data Streams",
    }


# ── Redshift ─────────────────────────────────────────────────────────────────

def redshift(region="us-east-1", description=None, **c) -> dict:
    """nodes, node_type (dc2.large|ra3.xlplus|ra3.4xlarge|ra3.16xlarge), pricing"""
    rc, rn = resolve_region(region)
    term = "Reserved_1Year_NoUpfront" if "reserved" in c.get("pricing", "").lower() else "OnDemand"
    calc = {
        "columnFormIPM": {"value": [{
            "Number of Nodes": {"value": str(c.get("nodes", 1))},
            "Instance Type":   {"value": c.get("node_type", "dc2.large")},
            "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
            "TermType":        {"value": term},
        }]},
    }
    return {
        "calculationComponents": calc,
        "serviceCode": "amazonRedshift",
        "region": rc, "regionName": rn,
        "estimateFor": "redshift",
        "version": "0.0.83",
        "description": description,
        "serviceName": "Amazon Redshift",
    }


# ── Bedrock ───────────────────────────────────────────────────────────────────

def bedrock(region="us-east-1", description=None, **c) -> dict:
    """
    Amazon on-demand model (default model). Token-rate based:
    requests_per_min, hours_per_day (default 24), input_tokens (per request),
    output_tokens (per request), prompt_caching (bool)
    Note: uses the default Amazon Bedrock model. Per-model pricing requires the
    model's selector hash; only the default Amazon model is wired here.
    """
    rc, rn = resolve_region(region)
    sub_calc = {
        "location":  {"value": "geo"},
        "tierIR":    {"value": "standard"},
        "modelSelectiongeoStan": {"value": "jqpXyMWar6dZCgJ4nRTHic6D040daCa-N81Kh52Jlac"},
        "selectedModelgeoStan":  {"value": "urNDBArH5pV5njuTwm41YJmDyeIrg_gD9kCMIHcQdLI"},
        "selectedModel_odgeoStan": {"value": "24444"},
        "avgRequestsPerMingeoStan":       {"value": str(c.get("requests_per_min", 1))},
        "hoursPerDayAtThisRategeoStan":   {"value": str(c.get("hours_per_day", 24))},
        "avgInputTokensPerRequestgeoStan":  {"value": str(c.get("input_tokens", 1000))},
        "avgOutputTokensPerRequestgeoStan": {"value": str(c.get("output_tokens", 1000))},
        "imageInputgeoStan":     {"value": "0"},
        "withPromptCachinggeoStan": {"value": "1" if c.get("prompt_caching") else "0"},
    }
    return {
        "serviceCode": "amazonBedrock",
        "region": rc, "regionName": rn,
        "estimateFor": "amazonBedrockClassesGroup",
        "version": "0.0.52",
        "description": description,
        "serviceName": "Amazon Bedrock",
        "subServices": [
            {"calculationComponents": sub_calc, "serviceCode": "amazon",
             "region": rc, "estimateFor": "Amazon", "version": "0.0.34", "description": None}
        ],
    }


# ── ElastiCache ───────────────────────────────────────────────────────────────

# EngineType selector hash (stable id for the "Design your own cache" node form).
_ELASTICACHE_ENGINE = "x4dSskWC2UA5R5dVtIkM0EjZJQKU02zll08quzox15U"


def elasticache(region="us-east-1", description=None, **c) -> dict:
    """
    engine: redis|valkey|memcached (default redis)
    nodes, node_type (cache.t3.micro|cache.m5.large|cache.r6g.large), pricing (on-demand|reserved)
    """
    rc, rn = resolve_region(region)
    eng = c.get("engine", "redis").lower()
    cache_engine = "Memcached" if "memcache" in eng else ("Valkey" if "valkey" in eng else "Redis")
    term = "Reserved_1Year_NoUpfront" if "reserved" in c.get("pricing", "").lower() else "OnDemand"
    node_type = c.get("node_type", "cache.m5.large")
    # ElastiCache families: Standard (t/m), Memory optimized (r), Network optimized (c7gn)
    base = node_type.replace("cache.", "").split(".")[0]
    fam = "Memory optimized" if base.startswith("r") else "Standard"
    col = {
        "Instance Type":   {"value": node_type},
        "Cache Engine":    {"value": cache_engine},
        "Number of Nodes": {"value": str(c.get("nodes", 1))},
        "undefined":       {"value": {"unit": "100", "selectedId": "%Utilized/Month"}},
        "Instance Family": {"value": fam},
        "TermType":        {"value": term},
    }
    return {
        "calculationComponents": {
            "EngineType":    {"value": _ELASTICACHE_ENGINE},
            "columnFormIPM": {"value": [col]},
        },
        "serviceCode": "amazonElastiCache",
        "region": rc, "regionName": rn,
        "estimateFor": "amazonElastiCache",
        "version": "0.0.81",
        "description": description,
        "serviceName": "Amazon ElastiCache",
    }


# ── Transfer Family ───────────────────────────────────────────────────────────

def transfer_family(region="us-east-1", description=None, **c) -> dict:
    """protocol (sftp|ftps|ftp), endpoints, upload_gb, download_gb"""
    rc, rn = resolve_region(region)
    calc = {
        "numberOfEndpoints": {"value": str(c.get("endpoints", 1))},
        "uploadData":        {"value": str(c.get("upload_gb", 10)),   "unit": "gb|month"},
        "downloadData":      {"value": str(c.get("download_gb", 10)), "unit": "gb|month"},
    }
    return {
        "calculationComponents": calc,
        "serviceCode": "awsTransferFamily",
        "region": rc, "regionName": rn,
        "estimateFor": "template",
        "version": "0.0.20",
        "description": description,
        "serviceName": "AWS Transfer Family",
    }


# ── Lightsail ─────────────────────────────────────────────────────────────────

# Lightsail bundle sizes -> the "operation" value the calculator expects.
_LS_BUNDLE = {
    "nano": "Bundle:0.5GB", "micro": "Bundle:1GB", "small": "Bundle:2GB",
    "medium": "Bundle:4GB", "large": "Bundle:8GB", "xlarge": "Bundle:16GB",
    "2xlarge": "Bundle:32GB",
    "0.5gb": "Bundle:0.5GB", "1gb": "Bundle:1GB", "2gb": "Bundle:2GB",
    "4gb": "Bundle:4GB", "8gb": "Bundle:8GB", "16gb": "Bundle:16GB", "32gb": "Bundle:32GB",
}


def lightsail(region="us-east-1", description=None, **c) -> dict:
    """bundle (nano|micro|small|medium|large|xlarge or 0.5GB..32GB), instances, os"""
    rc, rn = resolve_region(region)
    bundle = str(c.get("bundle", c.get("bundle_id", "small"))).lower().replace("_3_0", "").replace(" ", "")
    operation = _LS_BUNDLE.get(bundle, "Bundle:2GB")
    col = {
        "Operating System": {"value": "Windows" if "win" in c.get("os", "linux").lower() else "Linux"},
        "undefined":        {"value": {"unit": "100", "selectedId": "Hours/Month"}},
        "Number of Instances": {"value": str(c.get("instances", 1))},
        "operation":        {"value": operation},
    }
    return {
        "serviceCode": "amazonLightsail",
        "region": rc, "regionName": rn,
        "estimateFor": "amazonLightsail",
        "version": "0.0.69",
        "description": description,
        "serviceName": "Amazon Lightsail",
        "subServices": [
            {"calculationComponents": {"columnFormIPM": {"value": [col]}},
             "serviceCode": "lightsailVirtualServers", "region": rc,
             "estimateFor": "lightsailVirtualServers", "version": "0.0.4", "description": None}
        ],
    }


# ── Service registry ─────────────────────────────────────────────────────────

_SERVICES: dict[str, callable] = {
    "ec2": ec2,
    "s3": s3,
    "lambda": lambda_,
    "rds": lambda r, d, **c: rds(c.pop("engine","mysql"), r, d, **c),
    "rds mysql": lambda r, d, **c: rds("mysql", r, d, **c),
    "rds postgresql": lambda r, d, **c: rds("postgresql", r, d, **c),
    "rds postgres": lambda r, d, **c: rds("postgresql", r, d, **c),
    "rds oracle": lambda r, d, **c: rds("oracle", r, d, **c),
    "rds sqlserver": lambda r, d, **c: rds("sqlserver", r, d, **c),
    "rds sql server": lambda r, d, **c: rds("sqlserver", r, d, **c),
    "rds mariadb": lambda r, d, **c: rds("mariadb", r, d, **c),
    "aurora": lambda r, d, **c: aurora(c.pop("engine","mysql"), r, d, **c),
    "aurora mysql": lambda r, d, **c: aurora("mysql", r, d, **c),
    "aurora postgresql": lambda r, d, **c: aurora("postgresql", r, d, **c),
    "aurora postgres": lambda r, d, **c: aurora("postgresql", r, d, **c),
    "elb": elb,
    "alb": lambda r, d, **c: elb(r, d, **{**c, "lb_type": "alb"}),
    "nlb": lambda r, d, **c: elb(r, d, **{**c, "lb_type": "nlb"}),
    "load balancing": elb, "elastic load balancing": elb,
    "ebs": ebs, "efs": efs, "eks": eks,
    "cloudfront": cloudfront, "dynamodb": dynamodb,
    "cloudwatch": cloudwatch, "vpc": vpc,
    "network firewall": network_firewall, "networkfirewall": network_firewall,
    "elastic disaster recovery": disaster_recovery, "disaster recovery": disaster_recovery,
    "edr": disaster_recovery, "drs": disaster_recovery, "aws drs": disaster_recovery,
    "aws backup": aws_backup, "backup": aws_backup,
    "site-to-site vpn": site_to_site_vpn, "site to site vpn": site_to_site_vpn,
    "vpn": site_to_site_vpn, "vpn connection": site_to_site_vpn,
    "nat gateway": nat_gateway, "natgateway": nat_gateway, "nat": nat_gateway,
    "transit gateway": transit_gateway, "transitgateway": transit_gateway, "tgw": transit_gateway,
    "privatelink": privatelink, "private link": privatelink, "vpc endpoint": privatelink,
    "waf": waf, "guardduty": guardduty, "guard duty": guardduty,
    "inspector": inspector, "security hub": security_hub,
    "kms": kms, "cloudtrail": cloudtrail, "config": config,
    "fargate": fargate, "ecr": ecr,
    "codepipeline": codepipeline, "code pipeline": codepipeline,
    "codebuild": codebuild, "code build": codebuild,
    "api gateway": api_gateway, "apigateway": api_gateway,
    "route53": route53, "route 53": route53,
    "sqs": sqs, "sns": sns, "ses": ses,
    "cognito": cognito, "opensearch": opensearch,
    "kinesis": kinesis, "redshift": redshift,
    "bedrock": bedrock, "lightsail": lightsail,
    "elasticache": elasticache, "elastic cache": elasticache,
    "redis": lambda r, d, **c: elasticache(r, d, engine="redis", **c),
    "memcached": lambda r, d, **c: elasticache(r, d, engine="memcached", **c),
    "transfer family": transfer_family, "aws transfer": transfer_family,
}


# A short, friendly list of the common service names to suggest from.
_COMMON = [
    "EC2", "Lambda", "Fargate", "EKS", "Lightsail", "S3", "EBS", "EFS", "ECR",
    "RDS MySQL", "RDS PostgreSQL", "Aurora MySQL", "DynamoDB", "Redshift",
    "OpenSearch", "ElastiCache", "CloudFront", "Route53", "API Gateway",
    "ALB", "NLB", "VPC", "NAT Gateway", "Transit Gateway", "Network Firewall",
    "WAF", "GuardDuty", "KMS", "Cognito", "CloudWatch", "CloudTrail", "Config",
    "SQS", "SNS", "SES", "Kinesis", "Bedrock", "EDR", "AWS Backup", "CodeBuild",
]


def suggest_service(name: str, n: int = 3) -> list[str]:
    """Closest valid service names for a typo'd/unknown input."""
    import difflib
    key = (name or "").lower().strip()
    # match against all aliases, then map back to a clean display name
    hits = difflib.get_close_matches(key, _SERVICES.keys(), n=n, cutoff=0.5)
    seen, out = set(), []
    for h in hits:
        disp = h.title() if " " in h else h.upper() if len(h) <= 3 else h.capitalize()
        if disp.lower() not in seen:
            seen.add(disp.lower())
            out.append(h)
    return out


def build(service: str, region: str, description: str | None, config: dict) -> dict:
    key = (service or "").lower().strip()
    fn = _SERVICES.get(key)
    if not fn:
        sugg = suggest_service(key)
        hint = f" Did you mean: {', '.join(sugg)}?" if sugg else \
               " Try one of: EC2, S3, RDS MySQL, Lambda, DynamoDB, CloudFront…"
        raise ValueError(f"Unknown service '{service}'.{hint} "
                         f"(run list_services / GET /v1/services for the full list)")
    try:
        return fn(region, description, **config)
    except TypeError as e:
        # a bad/unknown config key for this service
        raise ValueError(f"Invalid config for '{service}': {e}") from e
