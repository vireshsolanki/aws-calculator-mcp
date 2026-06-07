#!/usr/bin/env python3
"""
AWS Pricing Calculator — REST API server.

This is the one component that needs Chromium (for cost-baking). Host it ONCE
(e.g. via the provided Dockerfile); every client — MCP, CLI, ChatGPT actions,
Zapier/Make, your own scripts — then talks plain HTTP and installs nothing heavy.

Endpoints
  GET  /health                 -> {"status": "ok"}
  GET  /v1/services            -> supported services + params
  GET  /v1/regions             -> supported regions
  POST /v1/estimate            -> create an estimate, returns a shareable link
       body: {estimate_name, groups[], services[], compute_costs}

Run locally:  uvicorn api_server:app --host 0.0.0.0 --port 8080
"""

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import core
from .services import REGIONS, _SERVICES

app = FastAPI(
    title="AWS Pricing Calculator API",
    version="1.0.0",
    description="Turn a service list into an official, shareable AWS Pricing "
                "Calculator link with real costs baked in.",
)

# Allow browser-based callers (ChatGPT custom GPTs, internal dashboards, etc.).
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)


class ServiceItem(BaseModel):
    service: str = Field(..., description="Service name, e.g. 'EC2', 'RDS MySQL'")
    region: str = Field("us-east-1", description="Region code, e.g. ap-south-1")
    description: str | None = Field(None, description="Optional label")
    config: dict[str, Any] = Field(default_factory=dict, description="Service params")


class GroupItem(BaseModel):
    group_name: str
    services: list[ServiceItem] = Field(default_factory=list)


class EstimateRequest(BaseModel):
    estimate_name: str = "My Estimate"
    prompt: str | None = Field(
        None, description="Plain-English infra description; we build the services for you. "
                          "e.g. '2 t3.large EC2, RDS MySQL db.m5.large 100GB, 500GB S3'")
    groups: list[GroupItem] = Field(default_factory=list)
    services: list[ServiceItem] = Field(default_factory=list)
    compute_costs: bool = True


@app.get("/health")
def health():
    from . import compute
    return {"status": "ok", "baking": compute.available()}


@app.get("/v1/regions")
def regions():
    return {"regions": [{"code": c, "name": n} for c, n in sorted(REGIONS.items())]}


@app.get("/v1/services")
def services():
    return {"services": sorted(set(_SERVICES.keys()))}


@app.post("/v1/estimate")
async def estimate(req: EstimateRequest):
    # Force LOCAL baking here even if AWS_CALC_API_URL is set elsewhere, so this
    # server never forwards to itself.
    saved = core.API_URL
    core.API_URL = ""
    try:
        result = await core.create_estimate(
            estimate_name=req.estimate_name,
            groups=[g.model_dump() for g in req.groups],
            services=[s.model_dump() for s in req.services],
            prompt=req.prompt,
            compute_costs=req.compute_costs,
        )
    finally:
        core.API_URL = saved
    return result


def run():
    """Console-script entry point: `aws-calc-api`."""
    import os
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))


if __name__ == "__main__":
    run()
