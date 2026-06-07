# AWS Pricing Calculator — Estimate Generator

[![PyPI](https://img.shields.io/pypi/v/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Describe your AWS setup in **plain English** and get back an **official, shareable
AWS Pricing Calculator link** — a real `https://calculator.aws/#/estimate?id=...`
with **real costs already computed and baked in**. No AWS account, no credentials,
no manual clicking, no JSON to write.

```
$ aws-calc --prompt "2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB"

✅ Monthly cost: $312.40 USD
🔗 https://calculator.aws/#/estimate?id=8422dc22a2849dbf798ab405385a7e5f32fcb055
```

Use it three ways — all from one install:
- **CLI** (interactive or one-liner) — for anyone, scripts, CI, `.exe`
- **MCP server** — inside Claude, Cursor, VS Code, any MCP client
- **REST API** (optional) — for ChatGPT actions, automation, other languages

> **Self-contained:** the module handles cost-baking itself — the browser engine it
> needs is **auto-downloaded on first run**. You install one pip package; nothing else.

---

## Contents
1. [Install](#1-install)
2. [Quick start — plain English](#2-quick-start--plain-english)
3. [Interactive mode](#3-interactive-mode)
4. [All CLI commands](#4-all-cli-commands)
5. [Use it in Claude / Cursor / IDEs (MCP)](#5-use-it-in-claude--cursor--ides-mcp)
6. [Use it from ChatGPT / automation (REST)](#6-use-it-from-chatgpt--automation-rest)
7. [Supported services & config](#7-supported-services--config)
8. [Commitment pricing (1yr / 3yr) & auto-scaling](#8-commitment-pricing--auto-scaling)
9. [How it works](#9-how-it-works)
10. [Limitations](#10-limitations)

---

## 1. Install

```bash
pipx install aws-calculator-mcp        # recommended (isolated)
# or
pip install aws-calculator-mcp
```

That's it. On the **first** estimate it downloads the Chromium engine once
(~150 MB) to compute costs; every run after is instant. (Debian/Ubuntu "externally
managed" error with `pip`? use `pipx`, or add `--break-system-packages`.)

## 2. Quick start — plain English

```bash
aws-calc --prompt "3 t3.large EC2 with 50GB each, an RDS MySQL db.m5.large 100GB \
multi-az, a 500GB S3 bucket, CloudFront 1TB, 10 lambdas with 2M requests, an ALB \
and an NLB in Mumbai"
```

It shows **exactly what it understood**, then returns the link with costs baked in:

```
   Understood from your prompt:
     • ec2 (instances=3, instance_type=t3.large, storage_gb=50)
     • rds mysql (instance_type=db.m5.large, storage_gb=100, deployment=multi-az)
     • s3 (storage_gb=500)
     ...
   Monthly cost: $782.00 USD
   🔗 https://calculator.aws/#/estimate?id=...
```

Add `--group` to organise the estimate into categories (Compute, Database, …).
Misspellings are tolerated (`lamda`, `buckit`, `dynmodb`, `cloud front` all work).

## 3. Interactive mode

Don't want to remember flags? Just run:

```bash
aws-calc -i        # or simply `aws-calc` with no arguments
```

It walks you through it:

```
Estimate name [My Estimate]: Prod Stack
AWS region (e.g. us-east-1, ap-south-1) [us-east-1]: ap-south-1
Group services by category? (y/n) [y]: y
Describe your infrastructure: 2 m5.large EC2, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB
→ 🔗 https://calculator.aws/#/estimate?id=...
```

## 4. All CLI commands

```bash
# plain-English prompt
aws-calc --prompt "2 m5.large ec2, rds mysql db.m5.large 100gb, 1tb s3"

# group into categories, pin a region
aws-calc --group --region ap-south-1 --prompt "ec2, rds, s3, alb, waf"

# interactive walkthrough
aws-calc --interactive

# one explicit service (full control)
aws-calc --service EC2 --region us-east-1 \
         --config '{"instances":2,"instance_type":"t3.large","storage_gb":50}'

# from a JSON file (full control over groups/services)
aws-calc --file estimate.json

# pipe a sentence in, or JSON in — JSON out for scripts/CI
echo "3 t3.medium ec2 and 1tb s3" | aws-calc --json
cat estimate.json | aws-calc --json

# fast draft link (skip cost-baking)
aws-calc --prompt "..." --no-costs

# name it
aws-calc --name "Client Proposal" --prompt "..."
```

Flags: `--prompt/-p`, `--interactive/-i`, `--group`, `--region/-r`, `--service/-s`,
`--config/-c`, `--file/-f`, `--name/-n`, `--no-costs`, `--json`.

## 5. Use it in Claude / Cursor / IDEs (MCP)

After `pipx install aws-calculator-mcp`, add to your MCP config
(`claude_desktop_config.json`, Cursor, VS Code Continue, Windsurf, …):

```json
{
  "mcpServers": {
    "aws-calculator": {
      "command": "aws-calc-mcp"
    }
  }
}
```

Zero-install variant (via uv): `"command": "uvx", "args": ["--from","aws-calculator-mcp","aws-calc-mcp"]`.

Then just chat: *"Create an AWS estimate: 3 t3.large web servers, an RDS MySQL
db.m5.large with 100 GB, a 500 GB S3 bucket, grouped by category."* The model calls
the `create_estimate` tool (which accepts structured services **or** a `prompt`,
plus `group`) and returns the link.

## 6. Use it from ChatGPT / automation (REST)

Optional — run the REST API yourself (only if you want an HTTP endpoint):

```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api                 # serves on :8080  (honors $PORT)
```

```bash
curl -X POST http://localhost:8080/v1/estimate -H "Content-Type: application/json" \
  -d '{"prompt": "2 m5.large EC2, RDS MySQL db.m5.large 100GB, 500GB S3", "group": true}'
```

Endpoints: `GET /health`, `GET /v1/services`, `GET /v1/regions`, `POST /v1/estimate`.
Interactive docs at `/docs`; OpenAPI at `/openapi.json` (import that into a **ChatGPT
Custom GPT Action** to use it from ChatGPT). Point other installs at it with
`export AWS_CALC_API_URL=http://your-host:8080` so they skip local baking.

## 7. Supported services & config

~50 services, tested against AWS's own pricing engine:

| Category | Services |
|----------|----------|
| Compute  | EC2, Lambda, Fargate, EKS, Lightsail |
| Storage  | S3, EBS, EFS, ECR |
| Database | RDS (MySQL, PostgreSQL, Oracle, SQL Server, MariaDB), Aurora (MySQL/PostgreSQL), DynamoDB, Redshift, OpenSearch, ElastiCache (Redis/Valkey/Memcached) |
| Network  | CloudFront, Route 53, API Gateway, ELB/ALB/NLB, VPC, Network Firewall, Site-to-Site VPN, NAT Gateway, Transit Gateway, PrivateLink |
| Security | WAF, GuardDuty, KMS, Cognito, Inspector, Security Hub |
| Mgmt     | CloudWatch, CloudTrail, Config |
| Messaging| SQS, SNS, SES, Kinesis |
| AI / DR  | Bedrock, Elastic Disaster Recovery (EDR/DRS) |
| Dev      | CodeBuild |

When writing JSON (`--file` or the MCP/REST `services`/`groups`), each service is
`{"service","region","description","config"}`. Common `config` keys:

```
EC2:        instances, instance_type, os, storage_gb, pricing, term, upfront, hours_per_day
Lambda:     requests, duration_ms, memory_mb
S3:         storage_gb, get_requests, put_requests, data_returned_gb
RDS *:      instance_type, storage_gb, deployment (single-az|multi-az)
Aurora:     engine (mysql|postgresql), nodes, instance_type
DynamoDB:   mode (provisioned|on-demand), read_capacity, write_capacity, storage_gb
ElastiCache:engine, nodes, node_type
CloudFront: data_transfer_gb, https_requests
API Gateway:http_requests_million
ALB/NLB:    load_balancers, data_processed_gb
```
Full list: `GET /v1/services`, or ask an MCP client to "list services".

## 8. Commitment pricing & auto-scaling

```jsonc
{"service":"EC2","config":{
  "instance_type":"m5.large", "instances":2,
  "pricing":"compute-savings",  // or instance-savings | reserved | on-demand | spot
  "term":"3yr",                 // 1yr | 3yr
  "upfront":"all"               // none | partial | all
}}
```
Verified: m5.large ×2 — On-Demand **$140** → Savings 1yr **$103** → 3yr **$71**.
Model part-time / auto-scaling fleets with `"hours_per_day": 5` or `"utilization": 30`.
RDS/Aurora/Redshift/ElastiCache accept `"pricing":"reserved"`.

## 9. How it works

The AWS calculator computes prices **client-side in the browser** and only stores
the numbers in a saved estimate — there's no public compute endpoint. So this tool:
builds the exact payload AWS expects (`services.py`) → POSTs it to AWS's `saveAs`
API → opens the draft in a headless browser, clicks **Update estimate** so AWS's own
engine computes costs, then **Share** to re-save with them baked in (`compute.py`).
Because it uses AWS's engine, numbers always match calculator.aws.

```
parser.py    plain English → services            core.py     build → save → bake
services.py  service + config → AWS payload       compute.py  headless-browser baking
server.py    MCP (stdio)   api_server.py REST     cli.py      CLI + interactive
```

## 10. Limitations

- A few services may show **$0** until you set a value on the page after opening:
  **AWS Backup** (nested form the save API can't reach), **Transfer Family**,
  **CodePipeline** (near-free), **EC2 *standard* Reserved** (use Savings Plans),
  **DynamoDB on-demand** (provisioned works).
- **Bedrock** uses the default Amazon model (token-rate based).
- The natural-language parser is heuristic — name services explicitly for best
  results (an MCP client like Claude parses free-form prose more flexibly).
- Cost-baking runs a headless browser locally (auto-installed). On a server, that's
  ~1–2 GB RAM during baking. If a host can't run it, you still get a working draft
  link (costs appear after one "Update estimate" click).

---

Issues & PRs: [github.com/vireshsolanki/aws-calculator-mcp](https://github.com/vireshsolanki/aws-calculator-mcp)
· MIT licensed · not affiliated with AWS (uses the public calculator.aws endpoints).
