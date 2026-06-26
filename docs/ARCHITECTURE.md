# AWS Calculator MCP — Architecture

How the tool works under the hood, from plain English to a live calculator link.

---

## Flow Diagram

```
User Input (plain English)
    ↓
Parser (services.py)
    • Tokenize and split clauses
    • Fuzzy-match service names
    • Extract quantities, units, configs
    ↓
Service Builders (services.py)
    • Generate AWS calculator payloads
    • Validate regional availability
    ↓
Draft Estimate (core.py + HTTP POST)
    • Save draft to AWS cloud
    • Returns draft ID
    ↓
Headless Browser (compute.py + Playwright)
    • Load draft estimate in calculator
    • Wait for JavaScript to compute costs
    • Click "Share" → "Agree and continue"
    • Intercept save response
    ↓
Final Estimate ID
    ↓
Shareable Link: https://calculator.aws/#/estimate?id={final_id}
```

---

## Component Details

### 1. Parser (`src/aws_calc_mcp/parser.py`)

**Goal:** Convert "2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3" into structured service specs.

**Key functions:**

- **`parse_prompt(text: str, region: str) -> list[ServiceSpec]`**
  - Main entry point
  - Splits input on delimiters: `. `, `,`, `and`, `with a/an`, `;`, `\n`, `plus`
  - Example: `"2 EC2..., RDS..., S3..."` → 3 clauses

- **`_service_matches(clause: str) -> dict[str, ServiceSpec]`**
  - Finds all non-overlapping service names in a clause
  - Longest-match wins: "api gateway" matches before "api"
  - Handles aliases: "rds mysql" → "rds mysql", "aurora postgres" → "aurora postgres"
  - Returns dict mapping service name → config dict

- **`_qty(clause: str) -> int`**
  - Extracts count before matching service name
  - Strips instance types (`t3.large`, `db.m5.large`) first
  - Strips storage sizes (`500GB`, `1TB`) first
  - Strips years (`2019`, `2024`) first
  - Finds leading count word or digit
  - Example: "2 t3.large EC2" → 2

- **`_instance_family(type_str: str) -> str`**
  - Extracts family from instance type
  - `t3.medium` → `t3`
  - `db.r6g.large` → `r6g`
  - Used for OpenSearch, ElastiCache instance family selection

- **`_snapshot(c: dict) -> tuple[str, str | None]`**
  - Detects snapshot frequency from config
  - Maps "daily" → "30" snapshots/month, "weekly" → "4", "monthly" → "1"
  - Returns (frequency, snapshot_gb)

- **`suggest_service(key: str) -> list[str]`**
  - Fuzzy-matches typos: "lamda" → "lambda", "buckit" → "s3"
  - Uses `difflib.get_close_matches()`
  - Suggests up to 3 alternatives

**Edge cases handled:**

- EC2 storage-only clauses fold into preceding EC2 (not a separate EBS entry)
- Windows + SQL Server OS detection (post-processing step)
- Multi-service phrases: "ALB NLB CloudFront" → 3 distinct services
- Bare EC2 from preamble dropped if detailed EC2s exist
- Filler phrases ignored: "use on-demand pricing", "generate a link"

---

### 2. Service Builders (`src/aws_calc_mcp/services.py`)

**Goal:** Convert parsed config into exact AWS calculator JSON payloads.

**Pattern:** Each service is a function that:
1. Takes `region`, `description`, and `**config` (service-specific options)
2. Returns a dict with `serviceCode`, `estimateFor`, `version`, `calculationComponents`

**Example: EC2 builder**

```python
def ec2(region="us-east-1", description=None, **c) -> dict:
    """instances, instance_type, os, storage_gb, snapshot_frequency, ..."""
    rc, rn = resolve_region(region)
    
    # config extraction
    instances = int(c.get("instances", 1))
    itype = c.get("instance_type", "t3.medium")
    os = os_map.get(c.get("os", "linux"))
    storage_gb = c.get("storage_gb", 30)
    snapshot_freq, snapshot_gb = _snapshot(c)
    
    # payload construction
    calc = {
        "numberOfInstances": {"value": str(instances)},
        "selectInstanceType": {"value": itype},
        "selectedOS": {"value": os},
        "storageAmount": {"value": str(storage_gb), "unit": "gb|NA"},
        ...
    }
    if snapshot_freq != "0":
        calc["snapshotFrequency"] = {"value": snapshot_freq}
        calc["snapshotChanged"] = {"value": str(snapshot_gb), "unit": "gb|NA"}
    
    return {
        "serviceCode": "amazonEc2",
        "region": rc, "regionName": rn,
        "estimateFor": "ec2Instance",
        "version": "0.0.172",
        "description": description,
        "serviceName": "Amazon EC2",
        "calculationComponents": calc,
    }
```

**Key structures:**

- **`calculationComponents`:** field name → `{"value": str, "unit": optional}`
  - Most fields are simple values: `{"value": "2"}`
  - Some have units: `{"value": "100", "unit": "gb|NA"}`
  - Some have selections (hash-based model options): `{"value": "hash...", "selectedId": "..."}`

- **Regional info:**
  - `resolve_region(region)` returns `(region_code, region_name)`
  - All region names are official AWS names: "US East (N. Virginia)", not "us-east-1"

- **Service codes discovered by intercepting live calculator:**
  - EC2: `amazonEc2`
  - RDS MySQL: `amazonRDSMySQLDB`
  - Lambda: `aWSLambda`
  - S3: `amazonSimpleStorageServiceGroup`
  - Bedrock: `amazonBedrock` (with sub-service `amazon`)
  - ~50 services total

**Verified field mappings:**

- **EBS storage type:** `"Storage General Purpose gp3 GB Mo"` (not `"Storage General Purpose GB Mo"` which is gp2)
- **NAT Gateway:** Regional model only (not per-gateway model), fields: `regionalNatGatewayCount`, `regionalNatGatewayAzCount`, `regionalNatGatewayDataProcessed`
- **OpenSearch:** `columnFormIPM_1` (data nodes) + `columnFormIPM_2` (master nodes) as arrays
- **RDS:** Instance family (not availability) selected via column picker
- **Bedrock:** Model selection via hard-coded hash for default Amazon model

---

### 3. Draft Estimate (`src/aws_calc_mcp/core.py`)

**Goal:** Save a grouped set of services to AWS cloud, get a draft ID back.

**Function: `save_estimate()`**

```python
async def save_estimate(name: str, title_config: dict, groups: dict) -> str:
    """
    groups = {
        "group-uuid-1": {"name": "Compute", "services": {
            "service-uuid-1": {payload}, ...
        }},
        "group-uuid-2": {"name": "Database", "services": {...}},
    }
    
    Returns: draft_id (hex string)
    """
    payload = {
        "estimateName": name,
        "groups": groups,
    }
    
    # POST to AWS calculator save API
    resp = await httpx.post(
        "https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs",
        json=payload,
        timeout=30,
    )
    return resp.json()["savedKey"]
```

**API endpoint discovery:**
- Intercepted from calculator.aws → DevTools → Network
- Not publicly documented
- Returns CloudFront-signed ID

**Group names sanitization:**
- Cannot contain `&`, `<`, `>`
- If parser finds these, `core.py` sanitizes (e.g., `& ` → ` and `)

---

### 4. Cost Baking (`src/aws_calc_mcp/compute.py`)

**Goal:** Load the draft estimate in a headless browser, wait for JavaScript to compute costs, save the finalized link.

**Function: `bake_costs()`**

```python
async def bake_costs(draft_id: str, timeout_ms: int = 180000) -> tuple[str, str]:
    """
    draft_id: from save_estimate()
    
    Returns: (final_id, costs_string)
    - final_id: can be used in https://calculator.aws/#/estimate?id={final_id}
    - costs_string: "$XXX/mo" or raw cost dict
    """
    # Install Chromium if needed
    if not chromium_installed():
        _install_chromium()
    
    async with async_playwright() as p:
        # Launch headless browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",  # container-safe
                "--disable-dev-shm-usage",  # container-safe
                "--disable-gpu",  # headless-friendly
            ]
        )
        page = await browser.new_page()
        
        # 1. Load the draft
        url = f"https://calculator.aws/#/estimate?id={draft_id}"
        await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
        
        # 2. Wait for JavaScript to compute costs
        await page.wait_for_timeout(5000)
        
        # 3. Click "Share" button
        await page.click("button:has-text('Share')")
        
        # 4. Click "Agree and continue" on consent modal
        await page.click("button:has-text('Agree and continue')")
        
        # 5. Intercept the POST request that saves the finalized estimate
        async def on_request(request):
            if "saveAs" in request.url and request.method == "POST":
                # Read the response
                resp = await request.response()
                body = await resp.json()
                final_id = body.get("savedKey")
                
                # Also fetch costs from the GET endpoint
                cost_resp = await httpx.get(
                    f"https://d3knqfixx3sbls.cloudfront.net/{final_id}",
                    timeout=30
                )
                costs = cost_resp.json().get("totalCost", "?")
                
                return final_id, costs
        
        page.on("requestfinished", on_request)
        
        # 6. Wait for the request
        # (The button click triggers the flow)
        await page.wait_for_timeout(10000)
        
        await browser.close()
        return final_id, costs
```

**Why headless browser?**
- AWS calculator computes costs in JavaScript (client-side)
- No public API to calculate costs
- The save API accepts payloads but doesn't compute
- Playwright is reliable, works in containers, can automate UI clicks

**Chromium installation:**
- `_install_chromium()` downloads Playwright's Chromium bundle (~150 MB)
- Runs once on first use, then cached
- `playwright install chromium` equivalent

**Container safety:**
- Flags: `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`
- Works in Docker, GitHub Actions, Render, etc.

---

### 5. CLI (`src/aws_calc_mcp/cli.py`)

**Entry points:**

- **`aws-calc --prompt "description"`** → parse + build + save + bake + print link
- **`aws-calc -i`** → interactive mode (ask for name, region, description)
- **`aws-calc-mcp`** → MCP server mode

**Interactive flow:**
```
Estimate name [My Estimate]: Production
AWS region [us-east-1]: ap-south-1
Group services by category? (y/n) [y]: y
Describe your infrastructure: 2 m5.large EC2, RDS MySQL 100GB, 500GB S3
→ [bake]
→ Cost: $352.13/mo
→ Link: https://calculator.aws/#/estimate?id=...
```

**MCP server:**
- Exposes tools: `create_estimate`, `list_services`, `list_regions`
- Callable from Claude, Cursor, VS Code via MCP protocol

---

### 6. REST API (`src/aws_calc_mcp/api_server.py`)

**Optional FastAPI server for automation.**

```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api  # http://localhost:8080
```

**Endpoints:**
- `POST /v1/estimate` — takes `{"prompt": "...", "region": "...", "group": bool}`
- `GET /v1/services` — lists supported services
- `GET /v1/regions` — lists supported regions
- `GET /docs` — Swagger UI
- `GET /openapi.json` — for custom GPT actions

---

## Key Design Decisions

### 1. Why Playwright instead of Selenium?
- **Playwright:** Faster, better async support, modern, works with Chromium/Firefox/WebKit
- **Selenium:** older, slower, more boilerplate
- Both work; Playwright is simpler

### 2. Why httpx instead of requests?
- **httpx:** async-first, cleaner API, built-in streaming support
- **requests:** sync-only, doesn't fit async/await pattern
- For blocking use cases, `httpx.Client()` works fine

### 3. Why fuzzy matching in parser?
- Typos are common: "lamda", "buckit", "dynmodb"
- Fuzzy match handles these without manual alias lists
- `difflib.get_close_matches()` is stdlib, low overhead

### 4. Why not use the calculator API directly?
- AWS does not expose a public cost-calculation API
- The calculator computes costs client-side in JavaScript
- The only way to get real costs is to run the JavaScript
- (The save API exists but doesn't trigger calculation)

### 5. Why plain English parser instead of JSON only?
- Lowers friction: most people describe infra in words
- Works well with AI assistants (Claude writes better English than JSON)
- Ambiguity can be resolved by the AI (not by parsing alone)
- Users can iterate: "make it cheaper" → AI suggests optimizations

---

## Data Flow Example

**Input:**
```
"2 t3.large EC2 with 50GB storage and daily snapshots,
 RDS MySQL db.m5.large 100GB, 500GB S3 bucket in ap-south-1"
```

**After parsing:**
```python
[
    ("ec2", {
        "instances": 2,
        "instance_type": "t3.large",
        "storage_gb": 50,
        "snapshot_frequency": "daily",
        "snapshot_changed_gb": 10,
    }),
    ("rds mysql", {
        "instance_type": "db.m5.large",
        "storage_gb": 100,
    }),
    ("s3", {
        "storage_gb": 500,
    }),
]
```

**After building (service payloads):**
```python
{
    "group-123": {
        "name": "Compute",
        "services": {
            "ec2-abc": {
                "serviceCode": "amazonEc2",
                "estimateFor": "ec2Instance",
                "version": "0.0.172",
                "calculationComponents": {...},
            }
        }
    },
    "group-456": {
        "name": "Database",
        "services": {
            "rds-def": {
                "serviceCode": "amazonRDSMySQLDB",
                "estimateFor": "mySQLDB",
                "version": "0.0.135",
                "calculationComponents": {...},
            }
        }
    },
    ...
}
```

**After save (draft):**
```
draft_id = "a7f3e42c8d..." (16-char hex)
```

**After bake (final):**
```
final_id = "bf18591f93861015bfb294e5ed164e514765cc42" (40-char hex)
costs = {"monthly": 352.13, "upfront": 0}
link = "https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42"
```

---

## Testing Strategy

**Unit tests:**
- Parser: typos, multi-service, regional names, unit extraction
- Builders: each service's payload correctness
- Snapshots: daily/weekly/monthly frequency mapping

**Integration tests:**
- End-to-end: prompt → estimate → verify costs match calculator

**Fixtures:**
- Real calculator links (hardcoded in tests)
- Expected costs (from calculator.aws, manual verification)

---

## Known Limitations

1. **AWS Backup:** Storage field is not reachable in the UI form (accordion collapse issue) → calculator always shows $0
2. **EC2 standard Reserved Instances:** Payload requires fields that cannot be auto-filled without completing the form in UI → use Savings Plans instead (identical pricing, works correctly)
3. **Step Functions, EventBridge:** Not in calculator → approximated with Lambda/SNS
4. **Some edge-case services:** May have optional fields not yet captured

---

## Future Improvements

- OCR or DOM parsing to detect calculated costs without Playwright
- Integration with Terraform/CloudFormation parsers
- Cost optimization suggestions ("consider Savings Plans")
- Region cost comparison tool
- Historical cost tracking
