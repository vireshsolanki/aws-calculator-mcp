# AWS Pricing Calculator — Estimate Generator

[![PyPI](https://img.shields.io/pypi/v/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/aws-calculator-mcp.svg)](https://pypi.org/project/aws-calculator-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Describe your AWS setup in plain English → get an official AWS Pricing Calculator
link with real costs already filled in.** No AWS account, no logins, no JSON.

```
$ aws-calc --prompt "2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB"

✅ Monthly cost: $352.13 USD
🔗 https://calculator.aws/#/estimate?id=03fecc46f00312e0f3e868b62365de5758b9621d
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
   🔗 https://calculator.aws/#/estimate?id=1096b9ed939063ec3e4e5ff0b16628c6b2ccc0da
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
→ $417.81/mo 🔗 https://calculator.aws/#/estimate?id=5c6523f2ed925c250ddfa2c90f84a4def7c36858
```

Interactive mode is best when you want a quick guided run from the terminal. It
accepts normal sentences, but for the most accurate results, describe one service
at a time and separate services with commas.

Good:

```text
3 Windows EC2 servers m6a.4xlarge with 300GB storage for 8 hours per month,
EDR with 4 disks and 2000GB storage,
1TB AWS data transfer
```

Risky:

```text
Need DR app in Hyderabad 3 windows servers 8 hours EDR 4 disks 2000GB transfer 1TB make it cheap
```

The risky version may still work, but if many numbers are close together, the
tool can confuse counts, hours, disk counts, storage, or transfer amounts. If you
use Cursor/Claude/another AI client, ask the AI to rewrite your request into a
clean service list before calling the MCP tool.

### 3) Inside Claude / Cursor / any MCP client

Add this to your MCP config:

```json
{
  "mcpServers": {
    "aws-cost-estimator": {
      "command": "aws-calc-mcp"
    }
  }
}
```

In **Cursor**:

1. Install the package: `pipx install aws-calculator-mcp`
2. Check the command works: `aws-calc-mcp`
3. Open Cursor Settings → MCP → Add server.
4. Use command: `aws-calc-mcp`
5. Restart Cursor if the tool does not appear immediately.

If Cursor cannot find the command, use the full path:

```bash
which aws-calc-mcp
```

Then use that value in config, for example:

```json
{
  "mcpServers": {
    "aws-cost-estimator": {
      "command": "/home/you/.local/bin/aws-calc-mcp"
    }
  }
}
```

For local development from this repository, point Cursor at your venv binary:

```json
{
  "mcpServers": {
    "aws-cost-estimator-local": {
      "command": "/absolute/path/to/aws-mcp-calculator/.venv/bin/aws-calc-mcp"
    }
  }
}
```

Then just chat:

> *"I'm building a small website with ~10k visitors. Suggest a budget AWS setup and
> create a pricing link."*

The assistant designs the stack and calls the tool — you get the official link back.

Quick verification prompt after adding it:

> *"Use the AWS cost estimator tool to create a draft estimate for 1 t4g.small EC2
> with 20GB and 100GB S3 in Mumbai."*

Expected shape of the response:

```text
Services: 2
Understood from your prompt:
  • ec2 (instances=1, instance_type=t4g.small, storage_gb=20)
  • s3 (storage_gb=100)
https://calculator.aws/#/estimate?id=...
```

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

## Prompt recommendations

You do not need perfect JSON or AWS expertise, but the estimate is easier to
validate when the prompt is specific.

- Put commas between services: `2 EC2..., RDS..., S3..., ALB...`
- Put the count next to the service: `3 EC2 servers`, `2 Aurora nodes`, `4 EDR disks`
- Put units on every number: `300GB storage`, `1TB data transfer`, `8 hours per month`
- Say the region plainly: `in Mumbai`, `in Hyderabad`, or `region ap-south-1`
- Use exact AWS sizes when you know them: `m6a.4xlarge`, `db.r6g.large`, `cache.r6g.large`
- For DR, say `EDR` or `DRS` when you mean AWS Elastic Disaster Recovery. Use plain `DR`
  only as context, for example `Hyderabad DR setup with EDR...`
- For EC2 pricing, prefer `1-year savings plan` or `3-year savings plan` over
  generic `reserved`
- After every run, check the `Understood from your prompt` lines before trusting
  the price

If the prompt is messy, this pattern works well:

```text
Estimate this in ap-south-2:
3 Windows EC2 servers m6a.4xlarge, 300GB storage each, 8 hours per month
EDR, 4 disks, 2000GB storage, 10 percent change rate
AWS data transfer, 1TB outbound
```

---

## Real examples — click to validate

Each prompt below produced a **real, live** AWS Pricing Calculator link. Open any
of them to verify the costs yourself:

**1. Vague idea** — `"a small website with a database and a 100GB bucket"` → $148.62/mo
https://calculator.aws/#/estimate?id=3bc90edb5879c1c8bda43ad2384ec052b0d69e49

**2. Budget blog** — `"cheapest setup: 1 t4g.small server with 20GB for a personal blog"` → $13.86/mo
https://calculator.aws/#/estimate?id=b3a7dbb5284a327014f7330d670d6a2c16fa385a

**3. Site + daily snapshot** — `"1 t4g.medium server 50GB with daily snapshot, plus a 100GB S3 bucket"` → $40.83/mo
https://calculator.aws/#/estimate?id=bff1a75683a9137aca838217b29e2e334db130ad

**4. Web app (grouped)** — `"3 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB multi-az, 500GB S3, an ALB, CloudFront 1TB"` → $641.24/mo
https://calculator.aws/#/estimate?id=8c3cf1097ccee1b08379067d882c064acb889503

**5. Serverless API (grouped)** — `"Lambda with 10M requests, DynamoDB, API Gateway, 200GB S3"` → $28.56/mo + $180 upfront
https://calculator.aws/#/estimate?id=0dc7dcc6a28c504943f3d18d2ecffd66a8f18ad7

**6. Enterprise (grouped)** — `"4 m5.xlarge EC2, Aurora MySQL db.r6g.large 2 nodes, Redis cache.r6g.large, CloudFront 2TB, WAF, GuardDuty, CloudTrail"` → $1,311.13/mo
https://calculator.aws/#/estimate?id=ddb66ce8d0a726a1e539dd7e742072717b084744

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
- **Interactive mode is guided, not magic** — it uses the same plain-English parser
  as the CLI. It handles common sentences, typos and missing commas, but very long
  mixed prompts can still be ambiguous. Commas and units make it much more reliable.
- A few calculator forms may need manual tweaks after opening the link (notably
  AWS Backup and EC2 *standard* Reserved — use Savings Plans instead).
- The natural-language reader is a helper; an AI client (Claude/ChatGPT) handles
  messy descriptions even better.

---

## Feedback

This is open source and improving through real-world prompts. If a generated
calculator link is wrong, please open a GitHub issue with:

- the prompt or structured service list you used
- the generated calculator link
- what you expected to see in the AWS calculator

The goal is to make this MCP reliable for AWS, DevOps, FinOps and AI-agent
workflows.

---

## Changelog

- **1.3.4** — Cleaner calculator payloads: no empty optional transfer sections, default EC2 boot storage for plain-English prompts, fixed Aurora node parsing, DRS/data-transfer regressions covered by tests.
- **1.3.0** — EBS snapshots (daily/weekly/monthly); simpler README + real example links; AI-tool integration guide.
- **1.2.x** — plain-English prompts, interactive mode, auto-grouping, self-contained baking (auto-installs the browser engine), multi-service phrases, friendly errors, typo tolerance.
- **1.0.x** — initial release: MCP server + CLI + REST API, ~50 AWS services, real baked-in costs.

---

Issues & feedback: [github.com/vireshsolanki/aws-calculator-mcp](https://github.com/vireshsolanki/aws-calculator-mcp)
· MIT licensed · not affiliated with AWS (uses the public calculator.aws endpoints).
