# FAQ — AWS Calculator MCP

---

## Installation

### Q: I got "externally managed Python" error on Ubuntu/Debian
**A:** Use `pipx` instead of `pip`:
```bash
pipx install aws-calculator-mcp
```

If `pipx` is not installed:
```bash
sudo apt install pipx
pipx install aws-calculator-mcp
```

Or use pip with the flag:
```bash
pip install --break-system-packages aws-calculator-mcp
```

### Q: The tool says "Executable doesn't exist" when I try to use it
**A:** Chromium needs to be installed. Run once:
```bash
python -m playwright install chromium
```

Or just run an estimate — it will install automatically on first use.

### Q: I installed it but `aws-calc` is not on my PATH
**A:** Find where it was installed:
```bash
which aws-calc
```

If it's not found, you may need to add the pip/pipx bin directory to your PATH:
```bash
# pipx (Linux/Mac)
export PATH="$HOME/.local/bin:$PATH"

# Windows
# Add C:\Users\YourName\AppData\Local\Programs\Python\Scripts to PATH manually
```

Add the export to your `.bashrc` or `.zshrc` to make it permanent:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Q: How do I set up the MCP server for Cursor?
**A:**
1. Install: `pipx install aws-calculator-mcp`
2. Check it works: `aws-calc-mcp` (should print MCP server info)
3. Open Cursor → Settings → MCP Servers → Add new server
4. Command: `aws-calc-mcp`
5. Restart Cursor

If Cursor can't find the command, use the full path:
```bash
which aws-calc-mcp
# Copy the output, e.g., /home/user/.local/bin/aws-calc-mcp
```

### Q: How do I set it up for Claude Desktop?
**A:**
1. Install: `pipx install aws-calculator-mcp`
2. Edit `~/.claude/mcp.json`:
   ```json
   {
     "mcpServers": {
       "aws-calculator": {
         "command": "aws-calc-mcp"
       }
     }
   }
   ```
3. Restart Claude Desktop

Note: The command must be on your PATH, or use the full path:
```json
{
  "mcpServers": {
    "aws-calculator": {
      "command": "/home/user/.local/bin/aws-calc-mcp"
    }
  }
}
```

### Q: Can I run this in a Docker container?
**A:** Yes. The tool includes container-safe Chromium flags:
```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    # Chromium dependencies
    libglib2.0-0 libnss3 libnspr4 libxss1 libasound2 libx11-xcb1 libxcb-dri3-0 \
    fonts-liberation libgdk-pixbuf2.0-0 libgtk-3-0 libxshmfence1 \
    xdg-utils libx11-6

RUN pip install aws-calculator-mcp

ENTRYPOINT ["aws-calc"]
```

Run:
```bash
docker run -it my-aws-calc --prompt "your infrastructure"
```

---

## Usage

### Q: What's the difference between `aws-calc --prompt` and `aws-calc -i`?
**A:**
- **`--prompt`:** One-liner for scripting. Costs are shown, then the link.
  ```bash
  aws-calc --prompt "2 EC2 m5.large, RDS MySQL 100GB"
  ```

- **`-i` (interactive):** Guided mode, asks questions step-by-step. Better for exploratory work.
  ```bash
  aws-calc -i
  # → Estimate name? Region? Description?
  ```

Use `--prompt` in automation, use `-i` when exploring manually.

### Q: Why is my estimate showing $0?
**A:** Reasons:
1. **Parser didn't understand:** Check the "Understood from your prompt" output. If it's empty or wrong, rephrase using commas and units.
2. **Service not fully supported:** A few services (AWS Backup, EC2 standard Reserved) have limitations. Check `ARCHITECTURE.md`.
3. **Calculator form issue:** Some services have optional fields that the tool doesn't auto-fill. Open the generated link and manually fill missing fields.

**Fix:**
- Rephrase: `"server 500GB storage"` → `"1 EC2 t3.medium with 500GB storage"`
- Use full service names: `"lambda"` → `"AWS Lambda"`
- Add units to everything: `"10"` → `"10GB"` or `"10 requests"` or `"10 instances"`

### Q: Can I use this to estimate costs for multiple regions at once?
**A:** Not with a single prompt, but you can chain commands:
```bash
aws-calc --prompt "2 m5.large EC2, RDS MySQL 100GB" --region us-east-1
aws-calc --prompt "2 m5.large EC2, RDS MySQL 100GB" --region ap-south-1
aws-calc --prompt "2 m5.large EC2, RDS MySQL 100GB" --region eu-west-1
```

For automation, use the REST API or Python library and loop over regions.

### Q: How accurate are these estimates?
**A:** Very accurate — the tool uses AWS's own calculator, so estimates match calculator.aws exactly.

However:
- Some services (AWS Backup, standard Reserved Instances) have UI-only fields that can't be auto-filled
- Complex commitments (savings plans with different upfront percentages) may need manual adjustment
- Costs change; refresh your links monthly

**Always verify:**
1. Open the generated calculator.aws link
2. Check the "Understood" output matches your infrastructure
3. Review the itemized costs before sharing

### Q: Can I export the estimate as a spreadsheet or PDF?
**A:** The calculator.aws website doesn't export directly. But you can:
1. Open the generated link
2. Right-click → Print / Save as PDF
3. Or take a screenshot

If you want programmatic export, file an issue on GitHub.

### Q: How do I share an estimate with someone who doesn't have the tool?
**A:** Just copy the calculator.aws link. Anyone can open it without installing anything:
```
https://calculator.aws/#/estimate?id=bf18591f93861015bfb294e5ed164e514765cc42
```

The link is permanent and shows the full itemized breakdown.

---

## Parser & Prompt Tips

### Q: What prompts work best?
**A:** Structured, with commas between services, units on numbers, and exact AWS sizes when you know them:

Good:
```
3 m5.large EC2 with 50GB storage each, RDS MySQL db.m5.large 100GB Multi-AZ, 500GB S3, ALB
```

Okay:
```
3 servers, database, 500GB storage, load balancer
```

Risky:
```
I need a highly available system with multiple servers and a database, maybe 500GB, for 10k users in three regions
```

**Pattern:**
- One service per clause (separated by commas)
- Exact AWS type next to service name
- Units on every number
- Regional names spelled out: `ap-south-1` or `Mumbai`, not `India`

### Q: The parser misunderstands my prompt. What can I ask Claude/Cursor to do?
**A:** Ask the AI to rewrite it first:

> *"I'll help you estimate AWS costs. Can you rewrite this infra description with comma-separated services, exact AWS instance types, and units on every number? [paste your messy description]"*

Claude will clean it up, then you can use it:
```bash
aws-calc --prompt "[Claude's rewritten version]"
```

### Q: Why does "500 GB EBS volume" create a 500-volume EBS?
**A:** The parser sees "500" before "EBS" and thinks it's the count. Fixed:
- Use: `"500GB EBS volume"` (now the parser strips "GB" before counting)
- Or: `"1 EBS volume with 500GB storage"`

### Q: Does the tool support typos?
**A:** Yes, common ones:
- `lamda` → `lambda`
- `buckit` → `s3`
- `dynmodb` → `dynamodb`
- `postgre` → `rds postgres`

If your typo isn't caught, you'll see "Unknown service" with suggestions.

### Q: Can I mix instance families in one estimate?
**A:** Yes:
```
2 t3.medium, 3 t3.large, 1 m5.xlarge
```

The parser handles `N instance_type` syntax.

### Q: How do I specify snapshots?
**A:** Include the frequency:
```
1 EC2 t3.medium with 50GB and daily snapshot
1 EC2 t3.medium with 50GB and weekly snapshot
1 EC2 t3.medium with 50GB and monthly snapshot
```

Or custom amount:
```
1 EC2 t3.medium with 50GB storage, 20GB snapshot daily
```

### Q: Can I specify savings plans or reserved instances?
**A:** Use these keywords:
```
1 t3.medium with 1-year savings plan
1 t3.medium with 3-year savings plan
1 RDS db.m5.large with 1-year reserved instance
```

Note: Standard Reserved Instances for EC2 still show $0 (UI-form-only fields). Use Savings Plans instead — same discount, works correctly.

---

## Services

### Q: Is [service name] supported?
**A:** Check:
```bash
aws-calc list  # or --list
```

Or see `README.md` → "What you can put in an estimate".

Current support: ~50 services including EC2, RDS, Lambda, S3, Bedrock, OpenSearch, Cognito, WAF, KMS, CloudWatch, CloudTrail, VPC, and more.

### Q: Why doesn't [service] work?
**A:** Reasons:
1. **Not in the tool yet:** Open an issue on GitHub, we'll add it.
2. **Not in the calculator yet:** AWS hasn't added it to calculator.aws. Example: Step Functions, EventBridge.
3. **Limitation:** AWS Backup and standard Reserved Instances need manual form completion.

### Q: Can I estimate costs for RDS Aurora?
**A:** Yes:
```
1 Aurora MySQL 2 nodes db.r6g.large
1 Aurora PostgreSQL 3 nodes db.r6g.xlarge
```

### Q: Can I mix regions in one estimate?
**A:** No. Use `--region` to set a default, then all services use that region:
```bash
aws-calc --prompt "2 EC2, RDS MySQL, S3" --region ap-south-1
```

All three services are estimated for Mumbai.

### Q: How do I estimate costs for multi-region setups?
**A:** Generate separate estimates per region, then add them manually:
```bash
aws-calc --prompt "your infra" --region us-east-1
aws-calc --prompt "your infra" --region eu-west-1
aws-calc --prompt "your infra" --region ap-south-1
```

Add the monthly costs together for the total.

---

## Advanced

### Q: Can I use this in a CI/CD pipeline?
**A:** Yes. Use the CLI with `--prompt`:
```bash
cost=$(aws-calc --prompt "2 EC2 t3.large, RDS MySQL 100GB" | grep "Monthly cost" | awk '{print $NF}')
echo "Estimated monthly cost: $cost"
```

Or use the REST API:
```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api &
curl -X POST http://localhost:8080/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "your infra", "region": "us-east-1"}'
```

### Q: Can I use this as a Python library?
**A:** Yes:
```python
import asyncio
from aws_calc_mcp.core import create_estimate
from aws_calc_mcp.compute import bake_costs
from aws_calc_mcp.services import build

async def estimate_cost(region, prompt):
    # Parse (manual for now, or integrate parser)
    services = [
        ("ec2", {"instances": 2, "instance_type": "t3.large"}),
        ("s3", {"storage_gb": 500}),
    ]
    
    # Build payloads
    groups = {}
    for svc, cfg in services:
        payload = build(svc, region, f"Compute", cfg)
        # ... group into dict ...
    
    # Save and bake
    draft = await create_estimate("My estimate", groups)
    final_id, costs = await bake_costs(draft)
    
    return f"https://calculator.aws/#/estimate?id={final_id}", costs

# Run
id, cost = asyncio.run(estimate_cost("us-east-1", "your prompt"))
print(cost)
```

### Q: Can I run this without Chromium?
**A:** No. Costs are calculated in the browser. If you want remote execution:
```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api --bind 0.0.0.0:8080
# Deploy to Render/Railway/heroku, then call the API from your local machine
```

The server handles Chromium, your client just POSTs.

### Q: How do I customize the output format?
**A:** For CLI, modify `cli.py` or use the REST API which returns JSON:
```bash
curl -X POST http://localhost:8080/v1/estimate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "..."}'
```

Response:
```json
{
  "services": [...],
  "link": "https://calculator.aws/#/estimate?id=...",
  "costs": {"monthly": 352.13, "upfront": 0}
}
```

---

## Troubleshooting

### Q: The browser hangs on "Agree and continue"
**A:** This means the button wasn't clicked. Reasons:
1. **Page took too long to load:** Increase timeout: `--timeout 300000` (300 seconds)
2. **Button selector changed:** calculator.aws UI updated. File an issue.
3. **Network issue:** Check your connection, retry.

### Q: "Executable doesn't exist" error
**A:** Chromium binary is missing or permissions are wrong.
```bash
python -m playwright install chromium
chmod +x ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome
```

### Q: Estimate link works but costs show $0
**A:** The calculator finished but couldn't compute. Check:
1. Open the link manually in a browser
2. Are services listed with costs? If yes, the tool cached an empty result. Delete cache and try again.
3. If no, the payload is invalid. File an issue with the prompt.

### Q: "Connection refused" when using REST API
**A:** Server not running.
```bash
pip install "aws-calculator-mcp[api]"
aws-calc-api  # starts on http://localhost:8080
```

Or specify a different port:
```bash
aws-calc-api --port 9000
curl http://localhost:9000/docs
```

### Q: Out of memory / Chromium crash
**A:** Headless browser can be memory-hungry. Options:
1. **Reduce headless tabs:** Don't run multiple estimates concurrently.
2. **Close other apps:** Free up RAM.
3. **Use remote API:** Deploy to a server with more memory.

### Q: "AWS calculator link format changed"
**A:** The tool intercepts the save response to get the final ID. If the format changed, file an issue with:
- The prompt you used
- The error message
- The generated draft ID (so we can test)

---

## Contributing

### Q: Found a bug. How do I report it?
**A:** Open a GitHub issue with:
- **Title:** Clear, specific problem
- **Prompt:** Exact text you used
- **Generated link:** The estimate we made
- **Expected:** What should happen
- **Actual:** What happened instead

Example:
```
Title: "EC2 with 3-year savings plan shows wrong discount"

Prompt: "1 t3.large with 3-year savings plan"

Generated: https://calculator.aws/#/estimate?id=...

Expected: ~$15/month (2/3 of on-demand)
Actual: Shows $30/month (same as on-demand)

Screenshot: [attached]
```

### Q: Want to add a new service?
**A:** See `CONTRIBUTING.md` → "New Service Builders".

### Q: Have a prompt that breaks the parser?
**A:** Open an issue with:
- The prompt
- What we parsed (wrong)
- What you expected

We'll improve the parser!

---

## More Help

- **GitHub Issues:** https://github.com/vireshsolanki/aws-calculator-mcp/issues
- **GitHub Discussions:** https://github.com/vireshsolanki/aws-calculator-mcp/discussions
- **Architecture deep dive:** See `ARCHITECTURE.md`
- **How to contribute:** See `CONTRIBUTING.md`
