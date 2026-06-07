# AWS Pricing Calculator — Estimate Generator

[![PyPI](https://img.shields.io/pypi/v/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-FFDD00?logo=buymeacoffee&logoColor=black)](https://www.buymeacoffee.com/vireshsolanki)

Turn a plain list of AWS services into an **official, shareable AWS Pricing
Calculator estimate** — a real `https://calculator.aws/#/estimate?id=...` link with
**real costs already computed and baked in**. No AWS account, no credentials, no
manual clicking.

```
You:  "1× t4g.large with 64 GB EBS, an Aurora MySQL db.r6g.large, and a 20 GB S3 bucket"
→     ✅ Monthly cost: $277.37 USD
      🔗 https://calculator.aws/#/estimate?id=b11f0bf1d0a6c46511ec9854d1eee49fcd820e93
```

Works as an **MCP server** (Claude, IDEs), a **REST API** (ChatGPT, automation,
any language), and a **CLI** (scripts, cron, `.exe`). Same engine behind all three.

---

## Table of contents

1. [Which setup do I want?](#1-which-setup-do-i-want)
2. [Quick start — hosted API (no Chromium for users)](#2-quick-start--hosted-api)
3. [Use it with Claude (MCP)](#3-use-it-with-claude-mcp)
4. [Use it with ChatGPT (Custom GPT action)](#4-use-it-with-chatgpt)
5. [Use it from any tool / automation (REST)](#5-use-it-from-any-tool--automation-rest)
6. [Use it from the command line / .exe](#6-use-it-from-the-command-line--exe)
7. [Writing an estimate (services & config)](#7-writing-an-estimate)
8. [Supported services](#8-supported-services)
9. [Commitment pricing (1yr / 3yr)](#9-commitment-pricing-1yr--3yr)
10. [How it works](#10-how-it-works)
11. [Architecture & files](#11-architecture--files)
12. [Limitations](#12-limitations)
13. [Maintenance](#13-maintenance)

---

## 1. Which setup do I want?

There is exactly **one heavy dependency** in the whole project: a headless browser
(Chromium), used to make AWS compute the costs. **You install it in exactly one
place — a server you host once — and then nobody else installs anything.**

| You are… | Do this | Installs |
|----------|---------|----------|
| An **org/admin** setting this up for others | Host the API ([§2](#2-quick-start--hosted-api)) | Docker (Chromium is inside the image) |
| An **end user** (Claude / ChatGPT / scripts) | Point at the hosted API | `mcp` + `httpx` only — **no browser** |
| A **solo user** who wants it all on one machine | Local mode ([§3 option B](#3-use-it-with-claude-mcp)) | Python + Playwright + Chromium |

> **Key promise:** with a hosted API, end users install **no Chromium and no
> Playwright** — they only talk HTTP. The browser lives solely inside the host.

---

## 2. Quick start — hosted API

Run this once on any box/VM/container host (it bundles Chromium for you):

```bash
git clone <this-repo> aws-calc && cd aws-calc
docker compose up -d            # builds + starts on port 8080
curl http://localhost:8080/health      # {"status":"ok","baking":true}
```

That's the whole server. Put it behind a domain/HTTPS if you want public access,
e.g. `https://aws-calc.yourcompany.com`. Now share that URL with everyone — they
use it from Claude, ChatGPT, scripts, etc. (sections below).

No Docker? Run it directly:

```bash
pip install ".[server]"          # fastapi + uvicorn + playwright
playwright install chromium
aws-calc-api                     # serves on :8080  (honors $PORT)
```

### Deploy on Render (one click)

This repo ships a `render.yaml` Blueprint and a `Dockerfile` (Chromium baked in).

1. Push the repo to GitHub.
2. Render → **New → Blueprint** → connect the repo → **Apply**.
   (Or **New → Web Service → Docker** and pick this repo.)
3. Render builds the image, injects `$PORT`, and exposes a public HTTPS URL like
   `https://aws-calc-api.onrender.com`. Health check: `/health`.
4. Use that URL as `AWS_CALC_API_URL` everywhere.

> **Memory:** Chromium needs headroom — use Render's **Standard** plan (2 GB).
> On 512 MB plans baking can OOM, in which case the API still returns a working
> *draft* link (costs appear after one "Update estimate" click). Same applies to
> Fly.io, Railway, ECS, Cloud Run, etc. — any Docker host works.

---

## 3. Use it with Claude (MCP)

### Option A — thin client (recommended, no browser)

Install the packaged module (lightweight — just `mcp` + `httpx`):

```bash
pipx install aws-calc-mcp        # or:  pip install aws-calc-mcp
```

This gives you three commands: `aws-calc-mcp` (MCP server), `aws-calc` (CLI),
`aws-calc-api` (REST server). Point the MCP at your hosted API in
`claude_desktop_config.json` (Claude Desktop) or your IDE's MCP config:

```json
{
  "mcpServers": {
    "aws-calculator": {
      "command": "aws-calc-mcp",
      "env": { "AWS_CALC_API_URL": "https://aws-calc.yourcompany.com" }
    }
  }
}
```

Zero-install alternative (no global install) using **uv**:

```json
{ "mcpServers": { "aws-calculator": {
  "command": "uvx", "args": ["aws-calc-mcp"],
  "env": { "AWS_CALC_API_URL": "https://aws-calc.yourcompany.com" } } } }
```

### Option B — all local (no server to host, but needs Chromium here)

```bash
pipx install "aws-calc-mcp[local]"     # adds Playwright
playwright install chromium
```

Same config, **without** the `AWS_CALC_API_URL` line.

> Installing from source instead of PyPI? `pip install -e .` (client) or
> `pip install -e ".[local]"` / `".[server]"`.

Then just ask Claude: *"Create an AWS estimate for 3 t3.large web servers, an RDS
MySQL db.m5.large with 100 GB, and a 500 GB S3 bucket."* Claude calls the
`create_estimate` tool and returns the link.

> Works in any MCP client: Claude Desktop, Claude Code, Cursor, VS Code (Continue),
> Windsurf, etc. — anything that speaks MCP.

---

## 4. Use it with ChatGPT

ChatGPT uses the REST API via a **Custom GPT Action** (no MCP needed):

1. Host the API ([§2](#2-quick-start--hosted-api)) on a public HTTPS URL.
2. ChatGPT → **Create a GPT** → **Configure** → **Actions** → **Add action**.
3. **Import from URL**: `https://aws-calc.yourcompany.com/openapi.json`
   (FastAPI auto-generates this — no schema to write by hand).
4. Save. Now tell your GPT: *"Estimate a serverless API: Lambda 100M requests,
   DynamoDB on-demand, 1 TB S3."* It calls `POST /v1/estimate` and returns the link.

The same OpenAPI spec works for any LLM-tool framework that imports OpenAPI
(LangChain, LlamaIndex, Zapier, Make, n8n, etc.).

---

## 5. Use it from any tool / automation (REST)

```bash
curl -X POST https://aws-calc.yourcompany.com/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "estimate_name": "My Stack",
    "services": [
      {"service": "EC2", "region": "ap-south-1",
       "config": {"instances": 2, "instance_type": "t3.large", "storage_gb": 50}},
      {"service": "S3", "region": "ap-south-1", "config": {"storage_gb": 500}}
    ]
  }'
```

```json
{ "ok": true, "url": "https://calculator.aws/#/estimate?id=…",
  "services": 2, "monthly": 110.66, "upfront": 0, "baked": true }
```

Endpoints: `GET /health`, `GET /v1/services`, `GET /v1/regions`,
`POST /v1/estimate`. Interactive docs at `/docs`.

---

## 6. Use it from the command line / .exe

```bash
# from a JSON file
aws-calc --file examples/estimate.json

# one-liner
aws-calc --name "Quick" --service EC2 --region ap-south-1 \
         --config '{"instances":2,"instance_type":"t3.large","storage_gb":50}'

# pipe JSON in / get JSON out (great for scripts & CI)
cat examples/estimate.json | aws-calc --json
```

Point at a hosted baker (no local Chromium) with `export AWS_CALC_API_URL=…`.

**Make a standalone `.exe`** (no Python on the target machine):

```bash
pip install pyinstaller
pyinstaller --onefile --name aws-calc src/aws_calc_mcp/cli.py
# dist/aws-calc.exe  — ships as a single file; set AWS_CALC_API_URL to skip Chromium
```

---

## 7. Writing an estimate

Every interface accepts the same shape:

```jsonc
{
  "estimate_name": "My Stack",
  "groups": [                          // optional — organise services by category
    {
      "group_name": "Compute",
      "services": [
        { "service": "EC2", "region": "us-east-1", "description": "Web tier",
          "config": { "instances": 2, "instance_type": "m5.large", "storage_gb": 50 } }
      ]
    }
  ],
  "services": [],                       // OR a flat list when you don't need groups
  "compute_costs": true                // bake real costs (default true)
}
```

- **service** — name (see [§8](#8-supported-services)); case-insensitive, aliases ok.
- **region** — code like `us-east-1`, `ap-south-1`, `eu-west-1` (`list_regions`).
- **config** — service-specific params ([§7 examples](#example-config-values)).

### Example config values

```
EC2:        instances, instance_type, os, pricing, term, upfront, storage_type,
            storage_gb, data_outbound_gb, utilization, hours_per_day
Lambda:     requests, duration_ms, memory_mb, arch
Fargate:    tasks, vcpu, memory_gb, storage_gb
S3:         storage_gb, storage_class, put_requests, get_requests, data_returned_gb
EBS:        volumes, storage_type, storage_gb
RDS *:      instance_type, storage_gb, deployment (single-az|multi-az), pricing
Aurora:     engine (mysql|postgresql), nodes, instance_type
DynamoDB:   mode (provisioned|on-demand), read_capacity, write_capacity, storage_gb
ElastiCache:engine (redis|valkey|memcached), nodes, node_type, pricing
CloudFront: data_transfer_gb, https_requests
API Gateway:http_requests_million, rest_requests_million
ALB/NLB:    load_balancers, data_processed_gb, requests_per_sec
VPC:        public_ips, nat_gateways, nat_data_gb, vpn_connections, tgw_attachments
Bedrock:    requests_per_min, input_tokens, output_tokens
EDR:        source_servers, disks, storage_gb, retention_days
WAF:        web_acls, rules_per_acl, requests_millions
CloudWatch: metrics, logs_gb, dashboards, alarms
```

Ask `list_services` (MCP) or `GET /v1/services` (REST) for the full set.

---

## 8. Supported services

~50 services, tested end-to-end against AWS's own pricing engine:

| Category | Services |
|----------|----------|
| Compute  | **EC2**, **Lambda**, **Fargate**, **EKS**, **Lightsail** |
| Storage  | **S3**, **EBS**, **EFS**, **ECR** |
| Database | **RDS** (MySQL, PostgreSQL, Oracle, SQL Server, MariaDB), **Aurora** (MySQL/PostgreSQL), **DynamoDB**, **Redshift**, **OpenSearch**, **ElastiCache** (Redis/Valkey/Memcached) |
| Network  | **CloudFront**, **Route 53**, **API Gateway**, **ELB/ALB/NLB**, **VPC**, **Network Firewall**, **Site-to-Site VPN**, **NAT Gateway**, **Transit Gateway**, **PrivateLink** |
| Security | **WAF**, **GuardDuty**, **KMS**, **Cognito**, **Inspector**, **Security Hub** |
| Mgmt     | **CloudWatch**, **CloudTrail**, **Config** |
| Messaging| **SQS**, **SNS**, **SES**, **Kinesis** |
| AI / DR  | **Bedrock**, **Elastic Disaster Recovery (EDR/DRS)** |
| Dev      | **CodeBuild** |

A ready-made **`standard_calc.py`** builds a full 12-service production web-app
estimate (auto-scaling EC2, ALB, API Gateway, WAF, CloudTrail, RDS, DynamoDB,
CloudFront, S3, SQS, Lambda, AWS Backup) — run it as a worked example.

---

## 9. Commitment pricing (1yr / 3yr)

EC2 supports Savings Plans / Reserved terms via `config`:

```jsonc
{ "service": "EC2", "config": {
    "instances": 2, "instance_type": "m5.large",
    "pricing": "compute-savings",   // or instance-savings | reserved | on-demand | spot
    "term": "3yr",                  // 1yr | 3yr
    "upfront": "all"                // none | partial | all
}}
```

Verified: m5.large ×2 — On-Demand **$140** → Savings 1yr **$103** → Savings 3yr **$71**.
On-demand also accepts `utilization` (%) or `hours_per_day` to model part-time /
auto-scaling fleets. RDS / Aurora / Redshift / ElastiCache accept `pricing: "reserved"`.

---

## 10. How it works

The AWS Pricing Calculator computes prices **client-side in the browser** from
static price files and only stores the resulting numbers in a saved estimate —
there is no public server-side compute endpoint. So this tool:

1. Builds the exact JSON payload AWS expects for each service (`services.py`).
2. `POST`s it to AWS's `saveAs` API → a draft estimate (`core.py`).
3. Opens the draft in headless Chromium, clicks **Update estimate** so AWS's own
   engine recomputes, then **Share → Agree** to re-save with real costs (`compute.py`).
4. Returns the final link — costs baked in, visible to anyone who opens it.

Because step 3 uses **AWS's own engine**, numbers always match calculator.aws and
there is no pricing engine to maintain. Step 3 is the only part needing a browser,
and it runs only on the host.

---

## 11. Architecture & files

```
pyproject.toml             Package metadata + entry points (aws-calc-mcp/-api, aws-calc).
src/aws_calc_mcp/
  services.py   Pure builders: service name + config → AWS payload JSON. No deps.
  core.py       Shared logic: build → save → bake. httpx only. Remote/local switch.
  compute.py    Optional cost-baking via Playwright/Chromium (host-only).
  server.py     MCP server (stdio) — thin wrapper over core.
  api_server.py REST API (FastAPI) — the hosted baker. Auto OpenAPI at /openapi.json.
  cli.py        Command-line interface; PyInstaller-friendly.
standard_calc.py           Worked 12-service example estimate.
Dockerfile / docker-compose.yml / render.yaml   One-command hosting (Chromium in image).
requirements*.txt          Optional pinned deps; pyproject is the source of truth.
```

Console commands (after `pip install`): **`aws-calc-mcp`** (MCP server),
**`aws-calc`** (CLI), **`aws-calc-api`** (REST server). Or run modules directly:
`python -m aws_calc_mcp.server`.

`AWS_CALC_API_URL` is the switch: set → clients forward to the hosted baker (no
local browser); unset → bake locally if Chromium is present, else return a draft
link (costs appear after one "Update estimate" click).

---

## 12. Limitations

- A few services may show **$0** until you set a value on the AWS page after opening:
  **AWS Backup** (backup-storage field is nested where the save API can't reach),
  **Transfer Family** (protocol hash), **CodePipeline** (near-free), **EC2 *standard*
  Reserved Instances** (use Savings Plans, which work), **DynamoDB on-demand**
  (provisioned works). They never break an estimate.
- **Bedrock** uses the default Amazon model (token-rate based); a specific
  third-party model (Claude, Llama…) needs that model's selector hash.
- The cost-baking step depends on AWS's (undocumented) calculator save API and
  client behavior. If AWS changes it, the host needs an update — clients don't.

---

## 13. Maintenance

AWS bumps the calculator's internal service `version`/`estimateFor` values over
time. If a service starts showing as read-only/incompatible or $0, refresh its
`version`/`estimateFor`/field names in `services.py` from a live capture (open the
service on calculator.aws, fill it, Share, and read the `saveAs` request payload in
DevTools → Network). Each builder in `services.py` documents its verified fields.

---

## Contributing & support

Issues and PRs welcome at
[github.com/vireshsolanki/aws-calculator-mcp](https://github.com/vireshsolanki/aws-calculator-mcp).

If this saved you time, you can support development:

<a href="https://www.buymeacoffee.com/vireshsolanki">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50" width="210">
</a>

> Not affiliated with Amazon Web Services. Uses the public calculator.aws endpoints.
> MIT licensed.
