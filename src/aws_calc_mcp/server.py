#!/usr/bin/env python3
"""
AWS Pricing Calculator — MCP server (stdio).

Thin wrapper over core.create_estimate. All estimate logic lives in core.py so
the MCP, the REST API (api_server.py) and the CLI (cli.py) behave identically.

No browser is required here: if AWS_CALC_API_URL is set, baking is delegated to
that hosted service; otherwise costs are baked locally only when Chromium exists.
"""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from . import core
from .core import create_estimate, format_result
from .services import REGIONS

app = Server("aws-calculator-mcp")


# ── Tool definitions ─────────────────────────────────────────────────────────

@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="create_estimate",
            description=(
                "Generate an official AWS Pricing Calculator estimate and return a "
                "shareable link (https://calculator.aws/#/estimate?id=...). "
                "Services can be organized into named groups (e.g. Compute, Database, Network). "
                "Each service needs: name, region, optional description, and config dict."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "estimate_name": {
                        "type": "string",
                        "description": "Title for this estimate",
                        "default": "My Estimate",
                    },
                    "compute_costs": {
                        "type": "boolean",
                        "description": (
                            "When true (default), bake real AWS-computed costs into the returned "
                            "link so it shows prices immediately. Requires Playwright/Chromium. "
                            "Set false to return a fast draft link (costs appear after clicking "
                            "'Update estimate' on the AWS page)."
                        ),
                        "default": True,
                    },
                    "groups": {
                        "type": "array",
                        "description": (
                            "List of service groups. Use groups to organise services by category "
                            "(e.g. Compute, Database, Network). Each group has a name and a list of services."
                        ),
                        "items": {
                            "type": "object",
                            "properties": {
                                "group_name": {
                                    "type": "string",
                                    "description": "Group label, e.g. 'Compute', 'Database', 'Network', 'Storage'"
                                },
                                "services": {
                                    "type": "array",
                                    "items": {"$ref": "#/$defs/service_item"},
                                },
                            },
                            "required": ["group_name", "services"],
                        },
                    },
                    "services": {
                        "type": "array",
                        "description": "Flat list of services (when no group organisation is needed)",
                        "items": {"$ref": "#/$defs/service_item"},
                    },
                },
                "$defs": {
                    "service_item": {
                        "type": "object",
                        "properties": {
                            "service": {
                                "type": "string",
                                "description": (
                                    "Service name. Supported: EC2, S3, Lambda, RDS, RDS MySQL, "
                                    "RDS PostgreSQL, RDS Oracle, RDS SQLServer, RDS MariaDB, "
                                    "Aurora, Aurora MySQL, Aurora PostgreSQL, ELB, ALB, NLB, "
                                    "EBS, EFS, EKS, CloudFront, DynamoDB, CloudWatch, VPC, "
                                    "WAF, GuardDuty, Inspector, Security Hub, KMS, CloudTrail, "
                                    "Config, Fargate, ECR, CodePipeline, CodeBuild, "
                                    "API Gateway, Route53, SQS, SNS, SES, Cognito, "
                                    "OpenSearch, Kinesis, Redshift, Bedrock, Lightsail, "
                                    "ElastiCache, Redis, Memcached, Transfer Family, "
                                    "Network Firewall, Site-to-Site VPN, NAT Gateway, "
                                    "Transit Gateway, PrivateLink, AWS Backup, "
                                    "Elastic Disaster Recovery (EDR/DRS)"
                                ),
                            },
                            "region": {
                                "type": "string",
                                "description": "Region code, e.g. us-east-1, ap-south-1, eu-west-1",
                                "default": "us-east-1",
                            },
                            "description": {
                                "type": "string",
                                "description": "Optional label shown in the estimate",
                            },
                            "config": {
                                "type": "object",
                                "description": (
                                    "Service-specific config. Common params per service:\n"
                                    "EC2: instances, instance_type, os, tenancy, workload, pricing, storage_type, storage_gb, data_inbound_gb, data_outbound_gb\n"
                                    "S3: storage_gb, storage_class, put_requests, get_requests, data_returned_gb\n"
                                    "Lambda: requests, duration_ms, memory_mb, arch, free_tier\n"
                                    "RDS/RDS MySQL/PostgreSQL: nodes, instance_type, storage_gb, storage_type, deployment, pricing\n"
                                    "Aurora: nodes, instance_type, storage_gb, engine, edition\n"
                                    "ELB/ALB/NLB: lb_type, load_balancers, data_processed_gb, connections_per_min, requests_per_sec\n"
                                    "EBS: volumes, storage_type, storage_gb, iops\n"
                                    "EFS: storage_gb, storage_type, throughput_mode\n"
                                    "EKS: clusters, hybrid_nodes\n"
                                    "CloudFront: data_transfer_gb, https_requests, http_requests\n"
                                    "DynamoDB: mode (provisioned|on-demand), read_capacity, write_capacity, storage_gb\n"
                                    "CloudWatch: metrics, logs_gb, dashboards, alarms\n"
                                    "VPC: public_ips, idle_ips, vpc_endpoints, nat_gateways, nat_data_gb, vpn_connections, tgw_attachments\n"
                                    "Network Firewall: endpoints, secondary_endpoints, data_processed_gb, advanced_inspection\n"
                                    "Site-to-Site VPN: connections, vpn_duration_hrs\n"
                                    "NAT Gateway: gateways, nat_data_gb\n"
                                    "Transit Gateway: attachments, tgw_data_gb\n"
                                    "PrivateLink: endpoints, endpoint_data_gb\n"
                                    "WAF: web_acls, rules_per_acl, requests_millions\n"
                                    "GuardDuty: s3_data_gb, management_events_million, s3_events, ec2_instances, ecs_instances\n"
                                    "Inspector: ec2_instances, lambda_functions, container_images\n"
                                    "Security Hub: accounts, security_checks, findings_ingested\n"
                                    "KMS: keys, symmetric_requests\n"
                                    "CloudTrail: events_million, write_trails, read_trails, s3_trails, lambda_trails\n"
                                    "Config: config_items, rule_evaluations\n"
                                    "Fargate: tasks, vcpu, memory_gb, storage_gb, arch, os\n"
                                    "ECR: storage_gb, data_inbound_gb, data_outbound_gb\n"
                                    "CodePipeline: pipelines_v1, pipelines_v2\n"
                                    "CodeBuild: builds_per_month, avg_build_min, compute_type\n"
                                    "API Gateway: http_requests_million, rest_requests_million, avg_size_kb\n"
                                    "Route53: hosted_zones, queries_million, health_checks\n"
                                    "SQS: requests_million, message_size_kb, fifo\n"
                                    "SNS: notifications_million\n"
                                    "SES: emails_sent_thousand, emails_received_thousand\n"
                                    "Cognito: maus, saml_maus\n"
                                    "OpenSearch: nodes, instance_type, storage_gb\n"
                                    "Kinesis: mode, shards, records_per_second, record_size_kb\n"
                                    "Redshift: nodes, node_type, storage_gb\n"
                                    "Bedrock: model, input_tokens, output_tokens\n"
                                    "Lightsail: bundle_id, instances\n"
                                    "ElastiCache/Redis/Memcached: engine, nodes, node_type, cache_size_gb, pricing\n"
                                    "Transfer Family: endpoints, upload_gb, download_gb"
                                ),
                            },
                        },
                        "required": ["service"],
                    }
                },
                "required": [],
            },
        ),
        types.Tool(
            name="list_services",
            description="List all supported AWS services with their config parameters.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="list_regions",
            description="List all supported AWS regions.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


# ── Handlers ─────────────────────────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "create_estimate":
            return await _handle_create(arguments)
        elif name == "list_services":
            return _handle_list_services()
        elif name == "list_regions":
            return _handle_list_regions()
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {e}")]


async def _handle_create(args: dict):
    name = args.get("estimate_name", "My Estimate")
    res = await create_estimate(
        estimate_name=name,
        groups=args.get("groups", []),
        services=args.get("services", []),
        compute_costs=args.get("compute_costs", True),
    )
    return [types.TextContent(type="text", text=format_result(name, res))]


def _handle_list_services():
    text = """Supported AWS Services
══════════════════════════════════════════

Compute
  EC2          instances, instance_type, os, pricing, storage_type, storage_gb, data_inbound_gb, data_outbound_gb
  Lambda       requests, duration_ms, memory_mb, arch (x86|arm64), free_tier
  Fargate      tasks, vcpu, memory_gb, storage_gb, arch, os
  EKS          clusters, hybrid_nodes
  Lightsail    bundle_id, instances

Storage
  S3           storage_gb, storage_class, put_requests, get_requests, data_returned_gb
  EBS          volumes, storage_type (gp3|gp2|io1|io2|st1|sc1), storage_gb, iops
  EFS          storage_gb, storage_type (standard|one-zone), throughput_mode
  ECR          storage_gb, data_inbound_gb, data_outbound_gb
  Redshift     nodes, node_type (dc2.large|ra3.xlplus), storage_gb

Database
  RDS MySQL / RDS PostgreSQL / RDS Oracle / RDS SQLServer / RDS MariaDB
               nodes, instance_type (db.t3.micro|db.m5.large), storage_gb,
               deployment (single-az|multi-az), pricing (on-demand|reserved)
  Aurora MySQL / Aurora PostgreSQL
               nodes, instance_type (db.r6g.large), storage_gb, edition
  DynamoDB     mode (provisioned|on-demand), read_capacity, write_capacity, storage_gb
  OpenSearch   nodes, instance_type, storage_gb
  ElastiCache / Redis / Memcached
               engine (redis|memcached), nodes, node_type (cache.t3.micro|cache.m5.large|cache.r6g.large),
               cache_size_gb, pricing (on-demand|reserved)

Network & Connectivity
  VPC          public_ips, idle_ips, vpc_endpoints, nat_gateways, nat_data_gb, vpn_connections, tgw_attachments
  Network Firewall   endpoints, secondary_endpoints, data_processed_gb, advanced_inspection
  Site-to-Site VPN   connections, vpn_duration_hrs
  NAT Gateway        gateways, nat_data_gb
  Transit Gateway    attachments, tgw_data_gb
  PrivateLink        endpoints, endpoint_data_gb
  ELB / ALB / NLB
               lb_type (alb|nlb|gwlb|classic), load_balancers, data_processed_gb,
               connections_per_sec, requests_per_sec
  CloudFront   data_transfer_gb, origin_transfer_gb, https_requests
  Route53      hosted_zones, queries_million, health_checks
  API Gateway  http_requests_million, rest_requests_million

Analytics / Streaming
  Kinesis      mode (on-demand|provisioned), shards, records_per_second, record_size_kb
  SQS          requests_million, message_size_kb, fifo (bool)
  SNS          notifications_million
  SES          emails_sent_thousand, emails_received_thousand

Security
  WAF          web_acls, rules_per_acl, requests_millions
  GuardDuty    s3_data_gb, management_events_million, s3_events, ec2_instances, ecs_instances
  Inspector    ec2_instances, lambda_functions, container_images
  Security Hub accounts, security_checks, findings_ingested, automation_rules
  KMS          keys, symmetric_requests
  Cognito      maus, saml_maus

Monitoring / Management
  CloudWatch   metrics, logs_gb, dashboards, alarms, log_insights_gb
  CloudTrail   events_million, write_trails, read_trails, s3_trails, lambda_trails
  Config       config_items, rule_evaluations, conformance_evaluations

Developer Tools
  CodePipeline pipelines_v1, pipelines_v2
  CodeBuild    builds_per_month, avg_build_min, compute_type (general1.small|general1.medium)
  Transfer Family
               endpoints, upload_gb, download_gb

AI / ML
  Bedrock      model, input_tokens, output_tokens

Pricing options (EC2):
  on-demand | savings-plans | reserved | spot
"""
    return [types.TextContent(type="text", text=text)]


def _handle_list_regions():
    lines = ["Supported AWS Regions\n" + "═"*40]
    for code, name in sorted(REGIONS.items()):
        lines.append(f"  {code:<22} {name}")
    return [types.TextContent(type="text", text="\n".join(lines))]


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (r, w):
        await app.run(r, w, app.create_initialization_options())


def run():
    """Console-script entry point: `aws-calc-mcp`."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
