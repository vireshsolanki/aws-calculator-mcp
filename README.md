# AWS Pricing Calculator — Estimate Generator

[![PyPI](https://img.shields.io/pypi/v/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Describe your AWS setup in plain English → get an official AWS Pricing Calculator
link with real costs already filled in.** No AWS account, no logins, no JSON.

```
$ aws-calc --prompt "2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB"

✅ Monthly cost: $312.40 USD
🔗 https://calculator.aws/#/estimate?id=8422dc22a2849dbf798ab405385a7e5f32fcb055
```

Use it from the **command line**, inside **Claude / Cursor / any AI IDE** (it's an MCP
server), or as a small **REST API**. One install does all three.

---

## Install

```bash
pipx install aws-calculator-mcp      # recommended
# or:  pip install aws-calculator-mcp
```

That's all. The first time you make an estimate it downloads a small browser
engine once (~150 MB) to read live prices — you don't install anything else.

*(On Ubuntu/Debian, if `pip` says "externally managed", use `pipx` or add
`--break-system-packages`.)*

---

## 3 ways to use it

### 1) Plain English (easiest)

```bash
aws-calc --prompt "1 t4g.medium server with 50GB and daily snapshot, plus a 100GB S3 bucket"
```
It prints exactly what it understood, then the link:
```
   Understood from your prompt:
     • ec2 (instances=1, instance_type=t4g.medium, storage_gb=50,
            snapshot_frequency=daily, snapshot_changed_gb=10)
     • s3 (storage_gb=100)
   Monthly cost: $40.83 USD
   🔗 https://calculator.aws/#/estimate?id=1b3909f3abc5ee560f181ab09e5782bcf96900ba
```
↑ that's a real link from this exact prompt — open it to validate.
- Add `--group` to organise by category (Compute, Database, Network…).
- Add `--region ap-south-1` (Mumbai) etc. Default is `us-east-1`.
- Typos are okay (`lamda`, `buckit`, `dynmodb` all work).

### 2) Interactive (it asks you)

```bash
aws-calc -i
```
```
Estimate name [My Estimate]: Prod
AWS region [us-east-1]: ap-south-1
Group services by category? (y/n) [y]: y
Describe your infrastructure: 2 m5.large EC2, RDS MySQL db.m5.large 100GB, an ALB
→ $412.34/mo 🔗 https://calculator.aws/#/estimate?id=744a3a78f61cccbe66e71f995e3f4a69290c4240
```

### 3) Inside Claude / Cursor / any MCP client

Add this to your MCP config (e.g. Claude Desktop `claude_desktop_config.json`,
or Claude Code / Cursor settings):

```json
{
  "mcpServers": {
    "aws-calculator": { "command": "aws-calc-mcp" }
  }
}
```
Restart the app, then just chat:
> *"I'm building a small website with ~10k visitors. Suggest a budget AWS setup and
> create a pricing link."*

The assistant designs the stack and calls the tool — you get the official link back.

> Tip: if the tool doesn't show up, the command isn't on PATH. Use the full path
> instead, e.g. `"command": "/home/you/.local/bin/aws-calc-mcp"` (find it with
> `which aws-calc-mcp`).

---

## What you can put in an estimate

~50 services. Just name them; sizes/counts are optional (sensible defaults apply):

| Type | Examples |
|------|----------|
| Compute | EC2, Lambda, Fargate, EKS, Lightsail |
| Storage | S3, EBS, EFS, ECR |
| Database | RDS (MySQL/PostgreSQL/Oracle/SQL Server/MariaDB), Aurora, DynamoDB, Redshift, OpenSearch, ElastiCache |
| Network | CloudFront, Route 53, API Gateway, ALB/NLB, VPC, NAT Gateway, Transit Gateway, Site-to-Site VPN, Network Firewall, PrivateLink |
| Security | WAF, GuardDuty, KMS, Cognito, Inspector, Security Hub |
| Other | CloudWatch, CloudTrail, Config, SQS, SNS, SES, Kinesis, Bedrock, AWS Backup, Disaster Recovery (EDR), CodeBuild |

**Handy things you can say:**
- **Instance type:** "t4g.medium", "db.m5.large", "cache.r6g.large"
- **Storage / transfer:** "50GB storage", "1TB data transfer"
- **Requests:** "2M requests", "10k messages per day"
- **Snapshots:** "daily snapshot of 20GB" (also weekly / monthly)
- **Savings:** "reserved 3 year", "savings plan 1 year"
- **Auto-scaling / part-time:** "runs 5 hours per day"

---

## Real examples — click to validate

Each prompt below produced a **real, live** AWS Pricing Calculator link. Open any
of them to verify the costs yourself:

**1. Vague idea** — `"a small website with a database and a 100GB bucket"` → ~$146/mo
https://calculator.aws/#/estimate?id=5ee317b0d334ca93f1ef10513235db7d9f74356a

**2. Budget blog** — `"cheapest setup: 1 t4g.small server with 20GB for a personal blog"` → ~$14/mo
https://calculator.aws/#/estimate?id=3f54f5ce9c3ec75651285396d365a0084728c360

**3. Site + daily snapshot** — `"1 t4g.medium server 50GB with daily snapshot, plus a 100GB S3 bucket"` → ~$41/mo
https://calculator.aws/#/estimate?id=d32b3a28e26e4283371cbe9e523438fe023389bb

**4. Web app (grouped)** — `"3 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB multi-az, 500GB S3, an ALB, CloudFront 1TB"` → ~$641/mo
https://calculator.aws/#/estimate?id=d7999f4669ad460084f4f50d25e060b3c69e5b92

**5. Serverless API (grouped)** — `"Lambda with 10M requests, DynamoDB, API Gateway, 200GB S3"` → ~$29/mo
https://calculator.aws/#/estimate?id=00acdb212a110d13966fad01174d091cfd3efd8a

**6. Enterprise (grouped)** — `"4 m5.xlarge EC2, Aurora MySQL db.r6g.large 2 nodes, Redis cache.r6g.large, CloudFront 2TB, WAF, GuardDuty, CloudTrail"` → ~$961/mo
https://calculator.aws/#/estimate?id=9043a6a1c002074063230ad1345628e474673d7d

---

## Use it with other AI tools

It's a standard **MCP server**, so any MCP-capable assistant can call it. The config
block is the same everywhere — `{"command": "aws-calc-mcp"}`:

| Tool | How to add it |
|------|---------------|
| **Claude Desktop** | Settings → Developer → Edit Config → add the `mcpServers` block → restart |
| **Claude Code** | `claude mcp add aws-calculator -- aws-calc-mcp` (or a project `.mcp.json`) |
| **Cursor** | Settings → MCP → Add server → command `aws-calc-mcp` |
| **Windsurf / Continue (VS Code)** | add the same `mcpServers` block to their MCP settings |
| **ChatGPT** (Custom GPT) | run `aws-calc-api`, then import `http://your-host:8080/openapi.json` as an Action |
| **n8n / Zapier / Make** | HTTP request node → `POST /v1/estimate` with `{"prompt": "..."}` |
| **LangChain / LlamaIndex / any agent** | call the REST endpoint, or shell out to the `aws-calc` CLI |

Once added, just ask the assistant in plain language:
> *"Design a budget AWS setup for a 10k-user app and create a pricing link."*

It picks the services and calls the tool — you get the official link back.

---

## Optional: run it as a REST API

Only if you want an HTTP endpoint (e.g. for ChatGPT actions or automation):

```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api                # http://localhost:8080
```
```bash
curl -X POST http://localhost:8080/v1/estimate -H "Content-Type: application/json" \
  -d '{"prompt": "2 m5.large EC2, RDS MySQL db.m5.large 100GB, 500GB S3", "group": true}'
```
Docs at `/docs`. For ChatGPT, import `/openapi.json` as a Custom GPT Action.

---

## Good to know

- **Costs come from AWS itself** — the tool fills the official calculator and reads
  the real numbers, so they match calculator.aws exactly.
- **Friendly errors** — unknown service → "did you mean…?"; it also tells you if it
  skipped a part it didn't understand.
- A few services may show **$0** until you tweak them on the page (AWS Backup,
  Transfer Family, EC2 *standard* Reserved — use Savings Plans instead).
- The natural-language reader is a helper; an AI client (Claude/ChatGPT) handles
  messy descriptions even better.

---

## Changelog

- **1.3.0** — EBS snapshots (daily/weekly/monthly); simpler README + real example links; AI-tool integration guide.
- **1.2.x** — plain-English prompts, interactive mode, auto-grouping, self-contained baking (auto-installs the browser engine), multi-service phrases, friendly errors, typo tolerance.
- **1.0.x** — initial release: MCP server + CLI + REST API, ~50 AWS services, real baked-in costs.

---

Issues & ideas: [github.com/vireshsolanki/aws-calculator-mcp](https://github.com/vireshsolanki/aws-calculator-mcp)
· MIT licensed · not affiliated with AWS (uses the public calculator.aws endpoints).
