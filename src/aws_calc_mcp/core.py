"""
Core estimate logic — shared by every interface (MCP, REST API, CLI).

Design for "no end-user install":
  • This module only needs `httpx` + `services.py` (pure Python, no browser).
  • Cost-baking (which needs Chromium) is OPTIONAL and isolated in `compute.py`.
  • Set env var AWS_CALC_API_URL to a hosted baking server and clients become
    thin: they forward the request over HTTP and get back a fully-baked link.
    End users then install nothing heavy — Chromium runs only on that one host.

Resolution order for `create_estimate`:
  1. If AWS_CALC_API_URL is set  -> forward to that hosted API (no local browser).
  2. Else if Playwright/Chromium is available -> bake locally.
  3. Else -> return a working draft link (costs appear after one "Update estimate").
"""

import os
import re
import json
import uuid
from datetime import datetime, timezone

import httpx

from .services import build, REGIONS

SAVE_API      = "https://dnd5zrqcec4or.cloudfront.net/Prod/v2/saveAs"
LOAD_API      = "https://d3knqfixx3sbls.cloudfront.net/"
ESTIMATE_BASE = "https://calculator.aws/#/estimate?id="
HEADERS = {
    "Content-Type": "application/json",
    "referer":      "https://calculator.aws/",
    "origin":       "https://calculator.aws",
    "user-agent":   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

# A hosted baking API (FastAPI from api_server.py). When set, clients forward to
# it instead of needing a local browser.
API_URL = os.environ.get("AWS_CALC_API_URL", "").rstrip("/")


# ── payload helpers ────────────────────────────────────────────────────────────

def _safe_text(text):
    # AWS rejects &, <, > in names, group names and descriptions.
    if not text:
        return text
    return text.replace("&", "and").replace("<", "(").replace(">", ")")


def _safe_group_name(name: str) -> str:
    return _safe_text(name) or "Group"


def _normalise_service(svc: dict) -> dict:
    out = dict(svc)
    out.setdefault("serviceCost", {"monthly": 0, "upfront": 0})
    out.setdefault("configSummary", "")
    for sub in out.get("subServices", []):
        sub.setdefault("serviceCost", {"monthly": 0, "upfront": 0})
    return out


def _normalise_group(grp: dict) -> dict:
    return {
        "name":          grp["name"],
        "services":      grp["services"],
        "groups":        {},
        "groupSubtotal": {"monthly": 0, "upfront": 0},
        "totalCost":     {"monthly": 0, "upfront": 0},
    }


def build_payload(groups_in: list | None, services_in: list | None):
    """
    Turn user-facing groups/services into AWS save-API dicts.
    Returns (top_services, groups_out, total_count, errors).
    """
    errors: list[str] = []
    top_services: dict = {}
    groups_out: dict = {}

    def add(entry: dict, target: dict):
        svc_name = (entry.get("service") or "").strip()
        if not svc_name:
            errors.append("A service entry is missing the 'service' field.")
            return
        region = entry.get("region", "us-east-1")
        desc   = _safe_text(entry.get("description"))
        config = dict(entry.get("config") or {})
        try:
            payload = build(svc_name, region, desc, config)
            target[f"{payload.get('serviceCode', 'svc')}-{uuid.uuid4()}"] = payload
        except ValueError as e:
            errors.append(str(e))

    for grp in (groups_in or []):
        gname = _safe_group_name(grp.get("group_name", "Group"))
        gid   = f"{re.sub(r'[^A-Za-z0-9]', '', gname) or 'Group'}-{uuid.uuid4()}"
        gsvcs: dict = {}
        for entry in grp.get("services", []):
            add(entry, gsvcs)
        groups_out[gid] = {"name": gname, "services": gsvcs}

    for entry in (services_in or []):
        add(entry, top_services)

    total = len(top_services) + sum(len(g["services"]) for g in groups_out.values())
    return top_services, groups_out, total, errors


async def save_estimate(name: str, top_services: dict, groups: dict) -> str:
    """POST to the AWS saveAs API and return the savedKey (draft id)."""
    norm_top = {k: _normalise_service(v) for k, v in top_services.items()}
    norm_groups = {}
    for gid, grp in groups.items():
        norm_svcs = {k: _normalise_service(v) for k, v in grp["services"].items()}
        norm_groups[gid] = _normalise_group({**grp, "services": norm_svcs})

    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    body = {
        "name": _safe_text(name) or "My Estimate",
        "services": norm_top,
        "groups": norm_groups,
        "groupSubtotal": {"monthly": 0, "upfront": 0},
        "totalCost":     {"monthly": 0, "upfront": 0},
        "support": {},
        "metaData": {"locale": "en_US", "currency": "USD",
                     "createdOn": created, "source": "calculator-platform"},
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(SAVE_API, headers=HEADERS, json=body)
        resp.raise_for_status()
    data  = resp.json()
    inner = data.get("body", "{}")
    if isinstance(inner, str):
        inner = json.loads(inner)
    return inner.get("savedKey") or inner.get("message", "").split()[-1]


# ── high-level entry point ──────────────────────────────────────────────────────

async def create_estimate(estimate_name: str = "My Estimate",
                          groups: list | None = None,
                          services: list | None = None,
                          compute_costs: bool = True,
                          prompt: str | None = None) -> dict:
    """
    Build → save → (optionally) bake an estimate.

    Provide either structured `groups`/`services`, OR a natural-language `prompt`
    (e.g. "2 t3.large EC2, an RDS MySQL db.m5.large 100GB, a 500GB S3 bucket").
    When `prompt` is given and no structured input, it's parsed for you.

    Returns: {ok, url, id, services, monthly, upfront, baked, warnings, parsed?, error?}
    """
    parsed_note = None
    if prompt and not groups and not services:
        from .parser import parse_prompt
        services, notes = parse_prompt(prompt)
        if not services:
            return {"ok": False,
                    "error": "Could not recognize any AWS services in the prompt. "
                             "Try naming services explicitly (EC2, S3, RDS, Lambda, …).",
                    "prompt": prompt}
        parsed_note = notes

    # 1. Remote mode — forward to a hosted baking API (no local browser needed).
    if API_URL:
        try:
            async with httpx.AsyncClient(timeout=240) as client:
                r = await client.post(
                    f"{API_URL}/v1/estimate",
                    json={"estimate_name": estimate_name, "groups": groups or [],
                          "services": services or [], "compute_costs": compute_costs},
                )
                r.raise_for_status()
                out = r.json()
                if parsed_note:
                    out["parsed"] = parsed_note
                return out
        except Exception as e:
            return {"ok": False, "error": f"Remote API ({API_URL}) failed: {e}"}

    # 2/3. Local mode.
    top, groups_out, total, errors = build_payload(groups, services)
    if total == 0:
        return {"ok": False, "error": "No valid services. " + "; ".join(errors),
                "warnings": errors}

    draft_id = await save_estimate(estimate_name, top, groups_out)
    final_id, totals, baked = draft_id, {}, False

    if compute_costs:
        try:
            from . import compute
            if compute.available():
                final_id, totals = await compute.bake_costs(draft_id)
                baked = bool(totals)
            else:
                errors.append("Cost baking unavailable locally (no Chromium). "
                              "Set AWS_CALC_API_URL to a hosted baker, or open the "
                              "link and click 'Update estimate' once.")
        except Exception as e:
            errors.append(f"Cost baking skipped ({e}). Link still works — click "
                          f"'Update estimate' on the page.")

    return {
        "ok": True,
        "url": f"{ESTIMATE_BASE}{final_id}",
        "id": final_id,
        "services": total,
        "monthly": totals.get("monthly", 0) if baked else None,
        "upfront": totals.get("upfront", 0) if baked else None,
        "baked": baked,
        "warnings": errors,
        "parsed": parsed_note,
    }


def format_result(name: str, res: dict) -> str:
    """Human-readable summary used by the MCP and CLI."""
    if not res.get("ok"):
        return f"❌ {res.get('error', 'Unknown error')}"
    lines = [f"✅ Estimate: **{name}**", f"   Services: {res['services']}"]
    if res.get("parsed"):
        lines.append("   Understood from your prompt:")
        lines += [f"     • {p}" for p in res["parsed"]]
    if res.get("baked"):
        m, u = res.get("monthly") or 0, res.get("upfront") or 0
        lines.append(f"   Monthly cost: ${m:,.2f} USD" + (f"  (upfront ${u:,.2f})" if u else ""))
        lines.append(f"   12-month total: ${m * 12 + u:,.2f} USD")
    lines += ["", f"🔗 {res['url']}", ""]
    if res.get("baked"):
        lines.append("Costs are computed and shown directly in the shareable link above.")
    else:
        lines.append("Open the link, then click 'Update estimate' to see live AWS costs.")
    if res.get("warnings"):
        lines += ["", "⚠️ Notes:"] + [f"  - {w}" for w in res["warnings"]]
    return "\n".join(lines)
