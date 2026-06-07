#!/usr/bin/env python3
"""
AWS Pricing Calculator — command-line interface.

Use it from shell scripts, CI, cron, or bundle it into an .exe (PyInstaller).
Reads a JSON spec describing the estimate and prints the shareable link.

Examples
  # from a file
  python cli.py --file estimate.json

  # from stdin (pipe JSON in)
  cat estimate.json | python cli.py

  # quick one-service estimate via flags
  python cli.py --name "Quick" --service EC2 --region ap-south-1 \
                --config '{"instances":2,"instance_type":"t3.large","storage_gb":50}'

  # machine-readable output
  python cli.py --file estimate.json --json

JSON spec format (same shape as the MCP / REST API):
  {
    "estimate_name": "My Stack",
    "groups": [
      {"group_name": "Compute", "services": [
        {"service": "EC2", "region": "us-east-1",
         "config": {"instances": 2, "instance_type": "m5.large"}}
      ]}
    ],
    "services": []
  }

Set AWS_CALC_API_URL to use a hosted baker (no local Chromium needed).
"""

import argparse
import asyncio
import json
import sys

from . import core


def _parse_args(argv):
    p = argparse.ArgumentParser(description="Create an AWS Pricing Calculator estimate link.")
    p.add_argument("--prompt", "-p", help="Describe your infra in plain English (we build the JSON).")
    p.add_argument("--interactive", "-i", action="store_true", help="Ask region / grouping / description step by step.")
    p.add_argument("--file", "-f", help="Path to a JSON estimate spec.")
    p.add_argument("--name", "-n", default="My Estimate", help="Estimate name.")
    p.add_argument("--service", "-s", help="Single service name (quick mode).")
    p.add_argument("--region", "-r", default=None, help="Region (overrides region(s) detected from a prompt).")
    p.add_argument("--config", "-c", default="{}", help="JSON config (quick mode).")
    p.add_argument("--group", action="store_true", help="Organise services into category groups.")
    p.add_argument("--no-costs", action="store_true", help="Skip cost baking (fast draft link).")
    p.add_argument("--json", action="store_true", help="Print the raw JSON result.")
    return p.parse_args(argv)


def _ask(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        ans = input(f"{question}{suffix}: ").strip()
    except EOFError:
        ans = ""
    return ans or default


def _interactive() -> dict:
    """Step-by-step prompts: name → region → grouping → description."""
    print("AWS Pricing Calculator — interactive estimate\n" + "-" * 44)
    name = _ask("Estimate name", "My Estimate")
    region = _ask("AWS region (e.g. us-east-1, ap-south-1)", "us-east-1")
    grp = _ask("Group services by category? (y/n)", "y").lower().startswith("y")
    print("\nDescribe your infrastructure in plain English.")
    print("e.g. '2 t3.large EC2 with 50GB, RDS MySQL db.m5.large 100GB, 500GB S3, an ALB'")
    desc = _ask("Infrastructure")
    if not desc:
        raise SystemExit("No description given.")
    return {"estimate_name": name, "prompt": desc, "region": region, "group": grp}


def _load_spec(args) -> dict:
    if args.interactive:
        return _interactive()
    if args.prompt:
        return {"estimate_name": args.name, "prompt": args.prompt,
                "region": args.region, "group": args.group}
    if args.file:
        with open(args.file) as fh:
            spec = json.load(fh)
        spec.setdefault("group", args.group)
        return spec
    if args.service:
        return {"estimate_name": args.name, "group": args.group, "services": [
            {"service": args.service, "region": args.region or "us-east-1",
             "config": json.loads(args.config)}]}
    if not sys.stdin.isatty():
        data = sys.stdin.read().strip()
        if data:
            if not data.lstrip().startswith("{"):
                return {"estimate_name": args.name, "prompt": data,
                        "region": args.region, "group": args.group}
            return json.loads(data)
    # no input at all -> fall into interactive mode (most user-friendly)
    if sys.stdin.isatty():
        return _interactive()
    raise SystemExit("No input. Use --interactive, --prompt \"...\", --file, --service, "
                     "or pipe text/JSON via stdin. See --help.")


async def _run(spec: dict, compute_costs: bool) -> dict:
    return await core.create_estimate(
        estimate_name=spec.get("estimate_name", "My Estimate"),
        groups=spec.get("groups", []),
        services=spec.get("services", []),
        prompt=spec.get("prompt"),
        group=spec.get("group", False),
        region=spec.get("region"),
        compute_costs=compute_costs,
    )


def main(argv=None):
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    spec = _load_spec(args)
    res = asyncio.run(_run(spec, compute_costs=not args.no_costs))
    if args.json:
        print(json.dumps(res, indent=2))
    else:
        print(core.format_result(spec.get("estimate_name", args.name), res))
    sys.exit(0 if res.get("ok") else 1)


if __name__ == "__main__":
    main()
