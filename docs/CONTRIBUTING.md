# Contributing to AWS Calculator MCP

Thanks for your interest in improving this tool. Here's how to help.

---

## Types of Contributions

### 1. **Bug Reports**
- Found a wrong estimate? Open an issue with:
  - The prompt you used
  - The generated calculator link
  - What you expected (and why)
  - A screenshot of the real calculator if possible

Example issue:
```
Title: EC2 storage_gb off by 50% for gp3

Prompt: "1 t3.medium with 500GB gp3 storage"

Generated: https://calculator.aws/#/estimate?id=...
Cost: $45/mo

Expected: $60/mo (based on manual calculator test)

I see the issue: storage_type is being set to "Storage General Purpose GB Mo" 
(gp2 string) instead of "Storage General Purpose gp3 GB Mo" (gp3 string).
```

### 2. **Parser Improvements**
The parser struggles with:
- Very long, rambling prompts
- Ambiguous quantities ("500" — is it storage or instance count?)
- Specialized domain phrases that aren't standard AWS naming

File: `src/aws_calc_mcp/parser.py`

**To improve:**
1. Add a test case in `tests/test_parser.py` that reproduces the issue
2. Fix the parser logic
3. Run tests: `pytest tests/test_parser.py -v`
4. Submit a PR with the failing test + fix

Example:
```python
# tests/test_parser.py
def test_parser_handles_mixed_ec2_and_storage():
    prompt = "2 servers with 100gb each, 1 database, 500gb data"
    services = parse_prompt(prompt)
    
    # assert correct interpretation
    assert len(services) == 3
    assert services[0] == ("ec2", {"instances": 2, "storage_gb": 100})
    assert services[1] == ("rds", {...})
    assert services[2] == ("s3", {"storage_gb": 500})
```

### 3. **New Service Builders**
Adding a new service takes ~50–150 lines of code.

**Steps:**

1. **Understand the service's calculator form:**
   - Go to https://calculator.aws/#/addService
   - Search for the service
   - Fill in test values
   - Open DevTools → Network tab
   - Click "Save and view summary" → "Share" → "Agree and continue"
   - Look for the `POST /v2/saveAs` request
   - Copy the JSON body — that's your payload template

2. **Extract the important fields:**
   ```json
   {
     "serviceCode": "amazonElastiCache",
     "estimateFor": "amazonElastiCache",
     "version": "0.0.81",
     "calculationComponents": {
       "numberOfInstances": {"value": "1"},
       "cacheNodeType": {"value": "cache.r6g.large"},
       "engineType": {"value": "...hash..."},
       ...
     }
   }
   ```

3. **Add the builder to `src/aws_calc_mcp/services.py`:**

```python
def elasticache(region="us-east-1", description=None, **c) -> dict:
    """
    engine: redis|memcached (default redis)
    nodes: number of cache nodes
    instance_type: e.g., cache.r6g.large
    """
    rc, rn = resolve_region(region)
    engine = c.get("engine", "redis").lower()
    nodes = str(c.get("nodes", 1))
    itype = c.get("instance_type", "cache.r6g.large")
    
    # Engine type hash (discovered from calculator form)
    engine_hashes = {
        "redis": "x4dSskWC2UA5R5dVtIkM0EjZJQKU02zll08quzox15U",
        "memcached": "...",
    }
    
    calc = {
        "numberOfInstances": {"value": nodes},
        "cacheNodeType": {"value": itype},
        "engineType": {"value": engine_hashes.get(engine, engine_hashes["redis"])},
        # ... other fields
    }
    
    return {
        "serviceCode": "amazonElastiCache",
        "region": rc, "regionName": rn,
        "estimateFor": "amazonElastiCache",
        "version": "0.0.81",
        "description": description,
        "serviceName": "ElastiCache",
        "calculationComponents": calc,
    }
```

4. **Register in `_SERVICES` dict:**
```python
_SERVICES = {
    # ... existing ...
    "elasticache": elasticache,
    "elasticache redis": elasticache,
    "redis": elasticache,
    "memcached": elasticache,
}
```

5. **Add tests:**
```python
# tests/test_services.py
def test_elasticache_builder():
    payload = elasticache(
        region="us-east-1",
        description="Test cache",
        engine="redis",
        nodes=2,
        instance_type="cache.r6g.large"
    )
    
    assert payload["serviceCode"] == "amazonElastiCache"
    assert payload["calculationComponents"]["numberOfInstances"]["value"] == "2"
    assert payload["version"] == "0.0.81"
```

6. **Verify on the real calculator:**
   - Generate an estimate using your new builder
   - Compare the generated link with a manual estimate
   - If costs don't match, debug the payload

7. **Submit a PR with:**
   - The new builder
   - Tests
   - Update to `_SERVICES` dict
   - One line added to `services.py` docstring

### 4. **Parser Improvements**
Add support for new phrases, better ambiguity resolution, regional name recognition.

File: `src/aws_calc_mcp/parser.py`

Example: Support "Fargate task" as alias for "fargate"
```python
# parser.py
_SERVICE_NAME_PATTERNS = {
    r"\bfargate\b|\bfargate\s+task": "fargate",
    r"\blambda\b|\blambda\s+function": "lambda",
    ...
}
```

### 5. **Documentation**
- Better examples
- Troubleshooting guide
- Video walkthrough
- Integration guides for specific tools (Terraform, Ansible, etc.)

---

## Development Setup

### Clone and install (editable mode):
```bash
git clone https://github.com/vireshsolanki/aws-calculator-mcp.git
cd aws-mcp-calculator
pip install -e ".[dev]"
```

### Run tests:
```bash
pytest tests/ -v
pytest tests/test_parser.py -k "test_ec2" -v  # specific test
```

### Run CLI locally:
```bash
python -m aws_calc_mcp.cli --prompt "your test prompt"
python -m aws_calc_mcp.cli -i  # interactive
```

### Run MCP server locally:
```bash
python -m aws_calc_mcp.server  # stdio mode (for testing in Claude/Cursor)
```

### Run REST API locally:
```bash
pip install ".[api]"
python -m aws_calc_mcp.api_server
# http://localhost:8080/docs
```

---

## Code Style

- **Type hints:** Use them for all function arguments and returns
- **Docstrings:** One-liner for service builders; longer for complex functions
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Formatting:** Black (run `black src/` before committing)

---

## Testing Requirements

Before submitting a PR:

1. **Run all tests:**
   ```bash
   pytest tests/ -v
   ```

2. **Test your changes manually:**
   ```bash
   python -m aws_calc_mcp.cli --prompt "your test case"
   ```

3. **If you added a service, generate a real estimate:**
   - Use the CLI or interactive mode
   - Compare with calculator.aws manually
   - Link the estimate in your PR description

4. **Check imports:**
   ```bash
   python -c "from aws_calc_mcp import core, services, parser; print('OK')"
   ```

---

## Submitting a PR

1. **Fork and create a branch:**
   ```bash
   git checkout -b fix/wrong-ec2-storage
   ```

2. **Commit with clear message:**
   ```
   Fix EC2 gp3 storage pricing (was using gp2 string)
   
   - Change st_map["gp3"] from "Storage General Purpose GB Mo" 
     to "Storage General Purpose gp3 GB Mo"
   - Update test_ec2_gp3_pricing to verify
   - Tested: estimate for 500GB gp3 now shows $60/mo (was $45/mo)
   ```

3. **Push and open a PR:**
   ```bash
   git push origin fix/wrong-ec2-storage
   ```

4. **PR description template:**
   ```markdown
   ## Problem
   EC2 with gp3 storage was being billed as gp2 (50% off).
   
   ## Solution
   Fixed the storage type string in st_map["gp3"].
   
   ## How to test
   aws-calc --prompt "1 t3.medium with 500GB gp3 storage"
   Expected: ~$60/mo
   Link: [your generated link]
   
   Manual verification: [link to calculator.aws estimate you created manually]
   
   ## Checklist
   - [x] Tests pass locally
   - [x] Manual estimate matches calculator.aws
   - [x] No breaking changes
   ```

---

## Common Tasks

### Debug a failed estimate:

1. **Get the exact prompt:**
   ```bash
   aws-calc --prompt "your prompt" 2>&1 | tee debug.log
   ```

2. **Check what was parsed:**
   ```bash
   # Add debug prints to parser.py
   print(f"Parsed services: {services}")
   ```

3. **Check the payload:**
   ```python
   from aws_calc_mcp.services import build
   payload = build("ec2", "us-east-1", "test", {"instances": 2})
   import json
   print(json.dumps(payload, indent=2))
   ```

4. **Compare with calculator.aws:**
   - Go to https://calculator.aws/#/addService
   - Add the service manually
   - Fill with same values
   - Save → compare the POST payload

### Add a new region:

1. **Update `services.py`:**
   ```python
   REGIONS = {
       # ... existing ...
       "ap-south-2": ("Hyderabad", "ap-south-2"),
   }
   ```

2. **Test:**
   ```bash
   aws-calc --prompt "1 EC2" --region ap-south-2
   ```

### Improve error messages:

Error messages are generated in:
- `parser.py` — unknown service, parsing failures
- `services.py` — invalid config for a service
- `core.py`, `compute.py` — API errors, timeout errors

Make them friendly and actionable:
```python
# Bad:
raise ValueError(f"Unknown service '{service}'")

# Good:
sugg = suggest_service(service)
hint = f" Did you mean: {', '.join(sugg)}?" if sugg else ""
raise ValueError(f"Unknown service '{service}'.{hint}")
```

---

## Questions?

Open an issue or start a discussion on GitHub. The community is here to help!

---

## Contributors

Special thanks to everyone who has reported bugs, improved the parser, or added new services. See `CHANGELOG.md` for individual contributions.
