import httpx
async def check(client, site):
    """Return (is_up, details) for one site."""
    details = {"name": site["name"], "url": site["url"], "status": None,
               "headers": {}, "body": "", "error": None}
    try:
        resp = await client.get(site["url"], timeout=site.get("timeout", 10))
        details["status"] = resp.status_code
        if resp.status_code != site.get("expected_status", 200):
            details["error"] = f"Expected HTTP {site.get('expected_status', 200)}, got {resp.status_code}"
            details["headers"] = dict(resp.headers)
            details["body"] = resp.text[:3000]
    except httpx.TimeoutException:
        details["error"] = "Request timed out"
    except httpx.HTTPError as e:
        details["error"] = f"{type(e).__name__}: {e}"
    return details["error"] is None, details