"""
Cost computation via the AWS Pricing Calculator's own engine.

AWS computes prices CLIENT-SIDE in the browser using static price files and
only stores the resulting numbers in the saved estimate. There is no public
server-side "compute" endpoint. So to bake real costs into a shareable link we:

  1. (already done) POST the estimate to the saveAs API  -> a draft link (costs = 0)
  2. open the draft in a headless browser
  3. click "Update estimate"  -> AWS recomputes every service with its own engine
  4. click "Share" -> "Agree and continue" -> AWS re-saves with the real costs
  5. capture the new savedKey -> a final link whose costs are baked in

This reuses AWS's exact pricing logic for every service, so the numbers always
match what a human would get on calculator.aws — no pricing engine to maintain.

Playwright/Chromium is only needed for this optional step. If it is not
installed, callers fall back to the draft link (costs appear after the user
clicks "Update estimate" once on the AWS page).
"""

import asyncio
import json

ESTIMATE_BASE = "https://calculator.aws/#/estimate?id="


class ComputeUnavailable(RuntimeError):
    """Raised when Playwright/Chromium is not available for cost baking."""


def available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def _install_chromium() -> None:
    """Download the Chromium engine once (only called when launch finds it missing)."""
    import subprocess
    import sys
    print("First run: downloading the Chromium engine for cost calculation "
          "(one-time, ~150 MB)...", file=sys.stderr)
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


async def bake_costs(draft_id: str, timeout_ms: int = 90_000) -> tuple[str, dict]:
    """
    Given a draft estimate id, drive AWS's own engine to compute costs and
    re-save. Returns (final_id, totals) where totals = {"monthly":..,"upfront":..}.

    Raises ComputeUnavailable if Playwright is not installed.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError as e:  # pragma: no cover
        raise ComputeUnavailable("playwright is not installed") from e

    url = f"{ESTIMATE_BASE}{draft_id}"
    saved_ids: list[str] = []
    # Container-friendly flags (sandbox / shared-memory restrictions).
    launch_args = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(headless=True, args=launch_args)
        except Exception as e:
            # Browser binary missing -> download it once, then retry.
            if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
                _install_chromium()
                browser = await p.chromium.launch(headless=True, args=launch_args)
            else:
                raise
        ctx = await browser.new_context(viewport={"width": 1600, "height": 1200})
        page = await ctx.new_page()

        async def on_resp(resp):
            if "saveAs" in resp.url:
                try:
                    body = resp.request.post_data
                    j = await resp.json()
                    inner = j.get("body")
                    if isinstance(inner, str):
                        inner = json.loads(inner)
                    key = inner.get("savedKey")
                    if key:
                        saved_ids.append(key)
                except Exception:
                    pass

        page.on("response", on_resp)

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            await page.wait_for_timeout(6000)

            # 1. Recompute with AWS's engine. Large estimates can take a while to
            #    render the button, so wait for it explicitly before clicking.
            update_btn = page.locator('button:has-text("Update estimate")').first
            await update_btn.wait_for(state="visible", timeout=60000)
            await update_btn.click()

            # 2. Wait until a non-zero cost appears (engine finished)
            for _ in range(20):
                await page.wait_for_timeout(2000)
                body = await page.inner_text("body")
                if any(
                    line.strip() not in ("", "0.00 USD")
                    for line in body.split("\n")
                    if "USD" in line
                ):
                    break

            # 3. Share -> Agree to persist the computed costs
            await page.locator('button:has-text("Share")').first.click()
            await page.wait_for_timeout(2500)
            await page.locator('button:has-text("Agree and continue")').first.click()

            # 4. Wait for the new saveAs to land
            for _ in range(15):
                await page.wait_for_timeout(2000)
                if saved_ids:
                    break
            await page.wait_for_timeout(2000)
        finally:
            await browser.close()

    if not saved_ids:
        # recompute happened but re-save didn't land; return the draft so the
        # user still gets a usable link
        return draft_id, {}

    final_id = saved_ids[-1]
    totals = await _fetch_totals(final_id)
    return final_id, totals


async def _fetch_totals(estimate_id: str) -> dict:
    import httpx

    load_url = f"https://d3knqfixx3sbls.cloudfront.net/{estimate_id}"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(load_url)
            data = r.json()
        return data.get("totalCost", {}) or {}
    except Exception:
        return {}
