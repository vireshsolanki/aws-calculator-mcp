# Launch Posts — AWS Calculator MCP

Use these templates to announce `aws-calculator-mcp` v1.3.4+ across platforms.

**Repository:** https://github.com/vireshsolanki/aws-calculator-mcp  
**PyPI:** https://pypi.org/project/aws-calculator-mcp/

---

## LinkedIn (Long-form, narrative)

### Post

I open-sourced **AWS Calculator MCP** — a tool that turns plain English AWS architecture descriptions into official AWS Pricing Calculator links with real costs already computed.

**The problem:** Estimating AWS costs requires either manual clicking through the calculator UI or writing JSON. Both are slow and error-prone. I wanted to ask Claude or Cursor: *"Design an AWS setup for 10k users"* and get a real, shareable calculator link back — not a guess.

**The solution:** A small MCP server that:
- Parses plain English (`"2 t3.large EC2, RDS MySQL 100GB, 500GB S3"`)
- Builds the exact AWS calculator payload
- Opens a headless browser, fills the form, and saves the live result
- Returns a shareable `calculator.aws/#/estimate?id=...` link with real costs

**It works as:**
- MCP server for Claude Desktop, Cursor, VS Code
- CLI: `aws-calc --prompt "your infra"`
- REST API (self-hosted or on Render)

**Proof — 10 real estimates I generated today for an AI/EdTech platform:**

| Setup | Cost | Link |
|-------|------|------|
| Growth tier (us-east-1) | $2,447/mo | [View](https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42) |
| Startup MVP (us-east-1) | $1,451/mo | [View](https://calculator.aws/#/estimate?id=3630aa55cf8ca74e381ae65efff332441bd425f3) |
| Enterprise (us-east-1) | $10,365/mo | [View](https://calculator.aws/#/estimate?id=4fb7883663e404ee0bd740678e1b731f4e7cd877) |
| Growth (ap-south-1) | $2,704/mo | [View](https://calculator.aws/#/estimate?id=bd8c6cd27195c61d73dae52b1a259e28292af94d) |
| Enhanced AI (us-east-1) | $4,613/mo | [View](https://calculator.aws/#/estimate?id=790e39be2063749d69d0b1654613b24148fe370f) |

Every link is real — open any to verify costs yourself on calculator.aws.

**Why open source:**
- AWS cost estimation should be auditable and shareable, not locked in spreadsheets
- FinOps, DevOps, and AI agents need reliable cost validation
- The community catches bugs and edge cases fast

**Latest release:** cleaner calculator payloads, default EC2 boot storage, fixed Aurora/DRS/EDR support, regression tests.

I built this because every infrastructure conversation I had ended with "let me check the calculator" — now I just ask Claude.

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp  
Try it: `pip install aws-calculator-mcp`

Open an issue if you find a broken estimate or have ideas for new services.

#AWS #OpenSource #FinOps #DevOps #MCP #CloudCost

---

## Reddit r/aws

### Title
I open-sourced a tool that generates real AWS Pricing Calculator links from plain English infrastructure descriptions

### Body

I built and open-sourced **AWS Calculator MCP**, a small tool that solves a friction point I hit every day: estimating AWS costs without clicking through the UI.

**What it does:**

Describe your AWS infrastructure in plain English:
```
2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB
```

It returns a real `calculator.aws` estimate link with costs already filled in:
```
https://calculator.aws/#/estimate?id=8c3cf1097ccee1b08379067d882c064acb889503
```

No JSON, no AWS account login, no manual form-filling. Click the link and you see the exact costs on the official calculator.

**How it works:**
- Parses plain English (handles typos: `lamda`, `buckit`, `dynmodb`)
- Builds the correct AWS calculator payload for each service
- Opens a headless browser, fills forms, clicks "Share", reads the response
- Returns the official calculator ID with real baked costs

**Proof — 10 real estimates from today:**

Standard growth tier (us-east-1): **$2,447/mo**  
https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42

Startup MVP (us-east-1): **$1,451/mo**  
https://calculator.aws/#/estimate?id=3630aa55cf8ca74e381ae65efff332441bd425f3

Enterprise (us-east-1): **$10,365/mo**  
https://calculator.aws/#/estimate?id=4fb7883663e404ee0bd740678e1b731f4e7cd877

India (ap-south-1): **$2,704/mo**  
https://calculator.aws/#/estimate?id=bd8c6cd27195c61d73dae52b1a259e28292af94d

Enhanced AI (Bedrock + HA OpenSearch): **$4,613/mo**  
https://calculator.aws/#/estimate?id=790e39be2063749d69d0b1654613b24148fe370f

**Supported:**
- ~50 AWS services: EC2, Lambda, RDS, DynamoDB, S3, CloudFront, Bedrock, OpenSearch, API Gateway, KMS, Cognito, WAF, VPC, CloudWatch, CloudTrail, and more
- All major regions
- Savings Plans and commitment pricing
- Snapshots, multi-AZ, reserved capacity

**Use cases:**
- **AI IDEs**: Tell Claude/Cursor your infra, get a real calculator link
- **FinOps teams**: validate cost models from plain language specs
- **DevOps automation**: generate cost estimates in CI/CD
- **Architecture review**: share precise calculator links instead of spreadsheets

**Install:**
```bash
pip install aws-calculator-mcp
aws-calc --prompt "your infrastructure description"
```

Or as an MCP server in Cursor/Claude:
```json
{ "mcpServers": { "aws-calc": { "command": "aws-calc-mcp" } } }
```

**Feedback wanted:** If the generated calculator link is wrong, please open a GitHub issue with the prompt and what you expected to see.

Repo: https://github.com/vireshsolanki/aws-calculator-mcp

---

## Reddit r/devops

### Title
Built an MCP server that generates AWS Pricing Calculator estimates from plain text infrastructure descriptions

### Body

For the DevOps folks: I open-sourced **AWS Calculator MCP**.

Problem: When designing infrastructure, you need to estimate costs fast. The AWS calculator is accurate but slow — clicking through 10+ forms for a single estimate is painful.

Solution: Type or paste your infra spec, get a real `calculator.aws` link back.

```bash
aws-calc --prompt "3 m5.xlarge EC2 for 8h/day, RDS Aurora MySQL 2 nodes, ElastiCache Redis, CloudFront 500GB, WAF"
```

Returns: A shareable calculator link with itemized costs, no manual work.

**Why this matters for DevOps:**
- Cost estimates in CI/CD pipelines (terraform plans → cost estimates)
- Validate proposed infrastructure changes before rolling out
- Share precise calculator links in runbooks and architecture docs
- No manual spreadsheet updates

**Real example from today's estimates:**

Growth tier (3 Lambdas, Bedrock, OpenSearch, RDS, DynamoDB, etc.): **$2,447/mo**  
Proof: https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42

Enterprise scale (same stack, 100k users, HA): **$10,365/mo**  
Proof: https://calculator.aws/#/estimate?id=4fb7883663e404ee0bd740678e1b731f4e7cd877

**Integration:**
- CLI for scripts/Ansible
- MCP server for Cursor/Claude (ask "what's the cost of 20 Fargate tasks?")
- REST API for automation

**Install:** `pip install aws-calculator-mcp`

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

Would love feedback from the DevOps community — especially on which service builders need work or which estimates don't match what you see in the real calculator.

---

## Reddit r/finops

### Title
Open-sourced a tool to generate AWS cost estimates programmatically (not clicking the calculator 50 times)

### Body

For FinOps and cost optimization teams: **AWS Calculator MCP**.

The ask: "Design an AWS infrastructure for N users" → you need to generate 5–10 calculator estimates to compare regions, commitment options, and architecture trade-offs.

Current workflow:
1. Copy the spec into Notepad
2. Click through the AWS calculator 10 times (one per estimate)
3. Paste each cost into a spreadsheet
4. Compare manually

New workflow:
```bash
aws-calc --prompt "Growth tier stack in us-east-1"
aws-calc --prompt "Same stack in ap-south-1"
aws-calc --prompt "Same stack in eu-west-1"
# → 3 real calculator links in seconds
```

**Use it for:**
- Regional cost comparisons (us-east-1 vs ap-south-1 vs eu-west-1)
- Commitment analysis (on-demand vs 1yr vs 3yr savings plans)
- Architecture trade-offs (serverless vs compute-heavy)
- Cost modeling for RFPs and proposals
- Audit trail (calculator links are shareable and point to real AWS data)

**Example — 10 different estimates from today:**

All cover: CloudFront, S3, WAF, Cognito, API Gateway, Lambda (3x), Bedrock, OpenSearch, RDS, DynamoDB, CloudWatch, CloudTrail, VPC.

| Scenario | Monthly | Link |
|----------|---------|------|
| Growth (us-east-1) | $2,447 | [View](https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42) |
| Startup MVP | $1,451 | [View](https://calculator.aws/#/estimate?id=3630aa55cf8ca74e381ae65efff332441bd425f3) |
| Enterprise | $10,365 | [View](https://calculator.aws/#/estimate?id=4fb7883663e404ee0bd740678e1b731f4e7cd877) |
| India (Mumbai) | $2,704 | [View](https://calculator.aws/#/estimate?id=bd8c6cd27195c61d73dae52b1a259e28292af94d) |
| Singapore | $2,847 | [View](https://calculator.aws/#/estimate?id=e6ca69da08c306a075a3428de8767d6cab8334f2) |
| Europe (Ireland) | $2,707 | [View](https://calculator.aws/#/estimate?id=42971e2bca7928b0175b1067a4632db36cf7401d) |
| US West (Oregon) | $2,447 | [View](https://calculator.aws/#/estimate?id=9c537c6a0d2f0e9e9e06d6e3cdc8c6bbd59fc8dd) |
| Enhanced AI (bigger Bedrock/OpenSearch) | $4,613 | [View](https://calculator.aws/#/estimate?id=790e39be2063749d69d0b1654613b24148fe370f) |
| India Startup | $1,611 | [View](https://calculator.aws/#/estimate?id=ed2b48126bc9e636f6eff0588d0bb979520c6bf1) |
| India Enterprise | $10,781 | [View](https://calculator.aws/#/estimate?id=4d9e1663620eb510ba9cc284dc9d296455f81269) |

Every link is a real calculator.aws estimate. Click any and see the itemized breakdown.

**For cost models:**
- Plain English specs are auditable and non-technical stakeholders can review them
- Calculator links are proof — you're not estimating, you're reading AWS's own prices
- Works for baseline, pessimistic, and optimistic scenarios

**Install:** `pip install aws-calculator-mcp`

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

If you find an estimate that doesn't match the real calculator, please open an issue. FinOps is about accuracy, so feedback is critical.

---

## Reddit r/Python

### Title
Built an MCP tool that generates AWS cost estimates from plain English

### Body

I built and open-sourced **AWS Calculator MCP** — a Python package that parses plain English AWS infrastructure descriptions and returns official AWS Pricing Calculator links with real costs computed.

**Why:** Every cost estimation workflow either requires JSON/CLI or manual calculator clicks. I wanted to ask Claude: *"What's the cost of 10 Fargate tasks, RDS, and S3?"* and get a real calculator link.

**How:**
1. Natural language parser (handles typos, fuzzy matching, multi-service clauses)
2. Service builders for ~50 AWS services (EC2, Lambda, RDS, Bedrock, OpenSearch, etc.)
3. Headless browser (Playwright) to drive the live calculator
4. Returns the shareable calculator ID

**Install:**
```bash
pip install aws-calculator-mcp
```

**Usage:**
```bash
# CLI
aws-calc --prompt "2 m5.large EC2, RDS MySQL 100GB, 500GB S3"

# Interactive
aws-calc -i

# Python code
from aws_calc_mcp.core import create_estimate
from aws_calc_mcp.compute import bake_costs
import asyncio

async def main():
    draft = await create_estimate("My estimate", ...)
    final_id, costs = await bake_costs(draft)
    print(f"https://calculator.aws/#/estimate?id={final_id}")

asyncio.run(main())
```

**MCP server for Claude/Cursor:**
```json
{ "mcpServers": { "aws-calc": { "command": "aws-calc-mcp" } } }
```

**Architecture:**
- `parser.py` — NLP with regex + difflib fuzzy matching
- `services.py` — service builders (1700+ lines, all 50 services)
- `compute.py` — Playwright headless baking
- `core.py` — orchestration + remote API support
- `cli.py` — interactive + prompt modes

**What works:**
- EC2 (all OS/SQL combos, snapshots, Savings Plans)
- RDS (MySQL, PostgreSQL, Oracle, SQL Server, MariaDB, Aurora)
- Lambda, DynamoDB, S3, CloudFront, Bedrock, OpenSearch
- Networking (VPC, NAT, VPN, Transit Gateway, PrivateLink)
- Observability (CloudWatch, CloudTrail)
- Security (WAF, KMS, Cognito, GuardDuty)
- ~50 services total

**Recent fixes:**
- EBS gp3 pricing (was being billed as gp2)
- NAT Gateway regional model (was double-counting)
- Windows+SQL Server OS combos
- Aurora node counts
- DRS/EDR payloads
- Savings Plans support

**Tests:**
- Parser regression tests (handles typos, multi-service, regional names)
- Service builder tests (payload correctness for each service)
- Integration tests (end-to-end baking)

**Contributing:**
- Add new services via `services.py` builders
- Improve NLP parser in `parser.py`
- Open issues with failing prompts

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

---

## X / Twitter — Long Thread

**Tweet 1:**
I open-sourced AWS Calculator MCP. 

Plain English infrastructure → official AWS Pricing Calculator links with real costs baked in.

"2 m5.large EC2, RDS MySQL 100GB, 500GB S3" → live cost estimate you can share.

Works as MCP server, CLI, or REST API.

Thread below 🧵

**Tweet 2:**
Problem: Estimating AWS costs means either:
- Manual: click through the calculator UI 10+ times
- Scripted: write JSON payloads for every service

Both are slow. I wanted to ask Claude: "Design for 10k users" and get a real calculator link back.

**Tweet 3:**
Solution: A small tool that:
1. Parses plain English (handles typos: lamda → Lambda)
2. Builds the exact AWS calculator payload for each service
3. Opens headless browser, fills forms, saves the result
4. Returns calculator.aws/#/estimate?id=... with real costs

**Tweet 4:**
Proof — 10 real estimates I generated today for an AI/EdTech platform:

🇺🇸 Growth tier (us-east-1): $2,447/mo
🇮🇳 India (ap-south-1): $2,704/mo
🤖 Enhanced AI: $4,613/mo
🏢 Enterprise: $10,365/mo

All real calculator.aws links. Click and verify yourself.

**Tweet 5:**
Supported:
- ~50 AWS services (EC2, Lambda, RDS, DynamoDB, S3, Bedrock, OpenSearch, API Gateway, KMS, Cognito, WAF, VPC, CloudWatch, CloudTrail...)
- All regions
- Savings Plans + commitment pricing
- Snapshots, multi-AZ, HA configs

**Tweet 6:**
Use cases:
- 🤖 AI IDEs: "Design a stack, cost it" (ask Claude, get a calculator link)
- 💰 FinOps: compare regional/commitment options programmatically
- 🏗️ DevOps: validate architecture changes with real costs
- 🤝 Sales: share calculator links instead of spreadsheets

**Tweet 7:**
Install: `pip install aws-calculator-mcp`

Works as:
- CLI: `aws-calc --prompt "your infra"`
- MCP server (Cursor, Claude, VS Code)
- REST API (self-host)

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

Open an issue if you find broken estimates. Community feedback wanted.

---

## X / Twitter — Short Version

I open-sourced AWS Calculator MCP.

Plain English AWS infra → official calculator.aws link with real costs.

Examples: 
- Growth tier: $2,447/mo
- Enterprise: $10,365/mo  
- India: $2,704/mo

All real. Click and verify.

Install: pip install aws-calculator-mcp

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

#AWS #OpenSource #MCP #DevOps #FinOps

---

## Hacker News — "Show HN"

### Title
Show HN: AWS Calculator MCP — Plain English → Official AWS Cost Estimates

### Body

I built AWS Calculator MCP, a tool that converts plain English infrastructure descriptions into official AWS Pricing Calculator links with real costs already filled in.

Problem: When designing AWS infrastructure, you need to estimate costs. The official calculator (calculator.aws) is accurate but requires manual form-filling — clicking through 10+ dropdowns for a single estimate is tedious.

Solution: Describe your infrastructure in plain English, get a real calculator link.

Example:
```
$ aws-calc --prompt "2 m5.large EC2, RDS MySQL db.m5.large 100GB Multi-AZ, 500GB S3, ALB, CloudFront 500GB"
$ https://calculator.aws/#/estimate?id=8c3cf1097ccee1b08379067d882c064acb889503
```

That link is real — open it and you'll see the itemized AWS costs on the official calculator.

How it works:
1. Natural language parser (handles typos, fuzzy matching, multi-service clauses)
2. Service builders for ~50 AWS services
3. Headless Playwright browser to drive the live calculator and save results
4. Returns the official calculator ID (shareable, proof that costs are real)

Works as:
- CLI: `aws-calc --prompt "your description"`
- MCP server for Claude, Cursor, VS Code (ask the AI assistant to estimate costs)
- REST API (for automation)

**Real examples from today:**

| Stack | Monthly | Link |
|-------|---------|------|
| Startup MVP | $1,451 | https://calculator.aws/#/estimate?id=3630aa55cf8ca74e381ae65efff332441bd425f3 |
| Growth tier | $2,447 | https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42 |
| Enterprise | $10,365 | https://calculator.aws/#/estimate?id=4fb7883663e404ee0bd740678e1b731f4e7cd877 |
| India (Mumbai) | $2,704 | https://calculator.aws/#/estimate?id=bd8c6cd27195c61d73dae52b1a259e28292af94d |

Every link is an official calculator.aws estimate. Costs match what you see on the live calculator.

Install: `pip install aws-calculator-mcp`

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

Why open source: AWS cost estimation should be auditable and shareable. FinOps, DevOps, and AI agents benefit from reliable, validated cost data. The community will catch bugs and edge cases faster than any single engineer.

Would love feedback from the HN community on broken estimates or missing services.

---

## Dev.to / Hashnode — Technical Deep Dive

### Title
I Built an MCP Server That Turns Plain English Into AWS Cost Estimates

### Body

**TL;DR:** I open-sourced AWS Calculator MCP, which parses plain English infrastructure descriptions and returns official AWS Pricing Calculator links with real costs. It works as an MCP server, CLI, or REST API.

```bash
aws-calc --prompt "2 t3.large EC2, RDS MySQL 100GB, 500GB S3"
→ $352.13/mo | https://calculator.aws/#/estimate?id=...
```

---

### The Problem

Every infrastructure conversation ends the same way:

> "Okay, so we need 3 m5.xlarge servers, a PostgreSQL database with 500GB, and some S3. How much does that cost?"

Current options:
1. **Manual:** Open calculator.aws, click through 10+ forms, screenshot each estimate, paste into a spreadsheet
2. **JSON:** Write a custom script that builds AWS calculator payloads (reverse-engineered, error-prone)
3. **Guess:** Use a cost calculator you found online (often wrong)

I wanted option 4: **Plain English + instant, verifiable result**.

---

### The Solution

AWS Calculator MCP accepts plain English and returns a real `calculator.aws` link:

```bash
aws-calc --prompt "1 t4g.medium with 50GB storage, daily snapshots, 100GB S3 bucket"
```

Output:
```
Understood from your prompt:
  • ec2 (instances=1, instance_type=t4g.medium, storage_gb=50, snapshot_frequency=daily)
  • s3 (storage_gb=100)

Monthly cost: $40.83 USD
Link: https://calculator.aws/#/estimate?id=bff1a75683a9137aca838217b29e2e334db130ad
```

Click that link — it's a real AWS calculator estimate, not a guess.

---

### How It Works

**1. Natural Language Parser**

File: `parser.py` (~400 lines)

The parser:
- Splits input by sentence breaks (`. `), commas, "and", "with a/an", etc.
- Detects service names using longest-match (e.g., "api gateway" → API Gateway, not "api")
- Fuzzy-matches typos (lamda → lambda, buckit → s3)
- Extracts quantities and units (e.g., "500GB" → 500)
- Handles OS + SQL Server combos (e.g., "Windows Server 2019 with SQL Standard")
- Folds storage-only EBS clauses into preceding EC2 entries

Example flow:
```python
text = "2 t3.medium servers with 50GB each, plus 100GB S3 bucket and daily snapshots"
clauses = split_on_delimiters(text)
# → ["2 t3.medium servers with 50GB each", "100GB S3 bucket", "daily snapshots"]

services = parse_clause("2 t3.medium servers with 50GB each")
# → [("ec2", {"instances": 2, "instance_type": "t3.medium", "storage_gb": 50})]
```

**2. Service Builders**

File: `services.py` (~1700 lines, 50 AWS services)

Each service has a builder that generates the exact AWS calculator payload:

```python
def ec2(region="us-east-1", description=None, **c) -> dict:
    """instances, instance_type, os, storage_gb, snapshot_frequency"""
    return {
        "serviceCode": "amazonEc2",
        "estimateFor": "ec2Instance",
        "version": "0.0.172",
        "calculationComponents": {
            "numberOfInstances": {"value": str(c["instances"])},
            "instanceType": {"value": c["instance_type"]},
            "selectedOS": {"value": os_map.get(c.get("os", "linux"))},
            ...
        }
    }
```

Services include: EC2, Lambda, RDS, DynamoDB, S3, Bedrock, OpenSearch, Cognito, WAF, API Gateway, KMS, CloudWatch, VPC, and ~40 more.

**3. Headless Baking**

File: `compute.py` (~250 lines)

The tricky part: AWS Pricing Calculator computes costs **client-side in the browser**. You can't just POST to an API and get a price back.

Solution:
```python
async def bake_costs(draft_id: str, timeout_ms: int = 180000):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Load the draft estimate
        await page.goto(f"https://calculator.aws/#/estimate?id={draft_id}")
        
        # Wait for the calculator to re-compute
        await page.wait_for_timeout(5000)
        
        # Click "Share" button
        await page.click("button:has-text('Share')")
        
        # Agree to ToS
        await page.click("button:has-text('Agree and continue')")
        
        # Wait for the POST request that saves the finalized estimate
        response = await page.wait_for_event("requestfinished")
        
        # Parse the response to get the finalized estimate ID
        final_id = extract_id_from_response(response)
        return final_id
```

The browser downloads on first run (~150 MB via Playwright).

**4. Orchestration**

File: `core.py` (~300 lines)

Ties it together:
```python
async def create_estimate(name: str, groups: dict) -> str:
    """Save an estimate draft to AWS calculator"""
    payload = {
        "estimateName": name,
        "groups": groups,  # grouped services from parser + builders
    }
    response = await httpx.post(
        "https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs",
        json=payload
    )
    return response.json()["savedKey"]

async def main():
    # 1. Parse user input
    services = await parse_prompt("your infrastructure")
    
    # 2. Build calculator payloads
    grouped_services = build_service_payloads(services)
    
    # 3. Save draft
    draft_id = await create_estimate("My estimate", grouped_services)
    
    # 4. Bake costs (browser)
    final_id, costs = await bake_costs(draft_id)
    
    # 5. Return shareable link
    print(f"https://calculator.aws/#/estimate?id={final_id}")
```

---

### Real Examples

**10 estimates generated today for an AI/EdTech platform:**

All cover: CloudFront, S3, WAF, Cognito, API Gateway, Lambda, Bedrock, OpenSearch, RDS, DynamoDB, CloudWatch, CloudTrail, VPC.

| Scenario | Monthly | Link |
|----------|---------|------|
| Startup MVP (us-east-1) | $1,451 | [View](https://calculator.aws/#/estimate?id=3630aa55cf8ca74e381ae65efff332441bd425f3) |
| Growth tier (us-east-1) | $2,447 | [View](https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42) |
| Enterprise (us-east-1) | $10,365 | [View](https://calculator.aws/#/estimate?id=4fb7883663e404ee0bd740678e1b731f4e7cd877) |
| Growth (ap-south-1) | $2,704 | [View](https://calculator.aws/#/estimate?id=bd8c6cd27195c61d73dae52b1a259e28292af94d) |
| Enhanced AI (Bedrock 50 RPM, HA OpenSearch) | $4,613 | [View](https://calculator.aws/#/estimate?id=790e39be2063749d69d0b1654613b24148fe370f) |

---

### Integration Points

**1. CLI**
```bash
aws-calc --prompt "your infrastructure"
aws-calc -i  # interactive
aws-calc --region ap-south-1 --group  # regional + grouped
```

**2. MCP Server (Claude, Cursor, VS Code)**
```json
{ "mcpServers": { "aws-calc": { "command": "aws-calc-mcp" } } }
```
Then ask Claude: *"Design a budget setup for 10k users and create an AWS cost estimate."*

**3. REST API**
```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api  # http://localhost:8080

curl -X POST http://localhost:8080/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "2 m5.large EC2, RDS MySQL 100GB, 500GB S3"}'
```

**4. Python Library**
```python
import asyncio
from aws_calc_mcp.core import create_estimate
from aws_calc_mcp.compute import bake_costs

async def main():
    # ... build groups ...
    draft = await create_estimate("My Estimate", groups)
    final_id, costs = await bake_costs(draft)
    print(f"https://calculator.aws/#/estimate?id={final_id}")

asyncio.run(main())
```

---

### Design Decisions

**Why headless browser and not API?**
- AWS Calculator computes costs client-side in JavaScript
- The save API accepts draft payloads but doesn't compute costs
- No public cost calculation API exists
- Playwright is battle-tested and works in containers

**Why plain English parser instead of JSON only?**
- Lowers friction — most people describe infra in words, not JSON
- Handles ambiguity better than hand-written JSON
- Typos are forgivable (`lamda` → lambda)
- Plays well with AI assistants (Claude can write better English than JSON)

**Why open source?**
- AWS cost estimation is foundational to infrastructure decisions
- Proprietary calculators and spreadsheets hide bias
- Community feedback improves accuracy
- Enables integration into broader FinOps workflows

---

### What's Next

- More services (CodePipeline, RDS Proxy, Glue, others)
- Better multi-service clause parsing
- Cost optimization suggestions ("consider Savings Plans")
- Region cost comparison (built-in tool)
- Integration with Terraform/CloudFormation parsers

---

### Try It

```bash
pip install aws-calculator-mcp

# CLI
aws-calc --prompt "2 t3.large EC2 with 50GB, RDS MySQL 100GB, ALB"

# Interactive
aws-calc -i

# Add to Cursor/Claude
# Settings → MCP → add command "aws-calc-mcp"
```

GitHub: https://github.com/vireshsolanki/aws-calculator-mcp

Feedback welcome. If you find an estimate that doesn't match calculator.aws, please open an issue with the prompt and expected cost.

---

## Discord / Slack — Community Post

**Title:** AWS Calculator MCP — Plain English AWS Cost Estimates

**Body:**

Yo, I open-sourced a tool called **AWS Calculator MCP**.

**What it does:** You describe your AWS setup in plain English → you get a real `calculator.aws` estimate link back with costs already computed. No clicking through the UI, no JSON, no guesses.

```
$ aws-calc --prompt "2 m5.large EC2, RDS MySQL 100GB, 500GB S3"
$ $352.13/mo
$ https://calculator.aws/#/estimate?id=...
```

That link is live. Click it and verify the costs yourself on calculator.aws.

**Use cases:**
- 🤖 Tell Claude/Cursor your infra, get a real cost link
- 💰 FinOps teams: compare regions/savings plans programmatically
- 🏗️ DevOps: validate architecture costs before deploying
- 📊 Sales: share calculator links instead of spreadsheets

**Install:** `pip install aws-calculator-mcp`

**Works as:**
- CLI
- MCP server for Claude, Cursor, VS Code
- REST API

**Proof — 10 real estimates:**

Startup: $1,451/mo  
Growth: $2,447/mo  
Enterprise: $10,365/mo  
India: $2,704/mo  
Enhanced AI: $4,613/mo  

All real calculator.aws links. Open and verify.

**GitHub:** https://github.com/vireshsolanki/aws-calculator-mcp

Feedback wanted. If you break it or find a wrong estimate, open an issue.

---

## Email Outreach Template

**Subject:** AWS Calculator MCP — Open-source tool for cost estimation (feedback wanted)

Hi [Name],

I built a small tool called **AWS Calculator MCP** and wanted to share it with you.

**What it does:**
- You describe your AWS infrastructure in plain English
- It generates a real AWS Pricing Calculator link with costs already computed
- Works as an MCP server (for Claude/Cursor), CLI, or REST API

**Example:**
```
aws-calc --prompt "2 m5.large EC2, RDS MySQL 100GB, 500GB S3, ALB"
→ $352.13/mo
→ https://calculator.aws/#/estimate?id=8c3cf1...
```

I open-sourced it because AWS cost estimation should be auditable and shareable, not locked in spreadsheets.

**Proof that it works:**
I generated 10 real estimates today for an AI/EdTech platform. All are live, shareable calculator.aws links. You can click any and verify the costs yourself.

- Startup MVP: $1,451/mo
- Growth tier: $2,447/mo
- Enterprise: $10,365/mo

[Full list of 10 + links in the GitHub README]

**If you work with:**
- AWS infrastructure design
- FinOps / cost optimization
- DevOps automation
- AI IDEs (Claude, Cursor)

...this tool might save you time.

**GitHub:** https://github.com/vireshsolanki/aws-calculator-mcp  
**PyPI:** https://pypi.org/project/aws-calculator-mcp/

Would love your feedback. If you find a broken estimate or have ideas for new services, please open an issue.

Thanks,  
[Your name]

---

## General Sharing Checklist

- [ ] Post LinkedIn (long-form narrative)
- [ ] Post Reddit r/aws (with proof links)
- [ ] Post Reddit r/devops (focus on automation/CI-CD)
- [ ] Post Reddit r/finops (regional/commitment analysis)
- [ ] Post Reddit r/Python (code structure)
- [ ] Post Reddit r/opensource (mission)
- [ ] Submit to Hacker News "Show HN"
- [ ] Write Dev.to / Hashnode article (technical deep dive)
- [ ] Share in DevOps / FinOps Slack / Discord communities (if self-promo allowed)
- [ ] Update GitHub topics: `aws`, `pricing`, `calculator`, `cost-estimation`, `mcp`
- [ ] Update PyPI description
- [ ] Email key contacts (DevOps influencers, FinOps leads, AWS experts)
- [ ] Consider Product Hunt (for broader visibility)

---

## Follow-up CTA

Best call to action across all platforms:

> Try it with a real AWS architecture you know. If the generated calculator link is wrong, open a GitHub issue with:
> - The prompt you used
> - The calculator link we generated
> - What you expected to see
>
> Community feedback makes this tool better.
