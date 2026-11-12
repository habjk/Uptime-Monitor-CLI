
import asyncio
import html
import os
import sys
import time

import httpx
import tomllib
from datetime import datetime
from ai_reporter import ai_report
from monitor import check
from email_sender import send_email

CONFIG = tomllib.load(open("sites.toml", "rb"))
INTERVAL = CONFIG.get("interval", 60)
FAILURE_THRESHOLD = CONFIG.get("failure_threshold", 2)
MODEL = CONFIG.get("model", "gemini-3.5-flash-lite")
EMAIL_FROM = CONFIG["email_from"]
EMAIL_TO = CONFIG["email_to"]
SITES = CONFIG["sites"]

RESEND_URL = "https://api.resend.com/emails"

for var in ("GEMINI_API_KEY", "RESEND_API_KEY"):
    if not os.environ.get(var):
        sys.exit(f"Please set the {var} environment variable.")
async def main():
    failures = {site["name"]: 0 for site in SITES}
    down_since = {}  # site name -> time it went down

    print(f"Monitoring {len(SITES)} site(s) every {INTERVAL}s. Press Ctrl+C to stop.")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        while True:
            results = await asyncio.gather(*(check(client, s) for s in SITES))
            print(f"[{datetime.now():%H:%M:%S}]")

            for is_up, d in results:
                name = d["name"]
                print(f"  {'UP  ' if is_up else 'DOWN'} {name}" + ("" if is_up else f" - {d['error']}"))

                if is_up:
                    if name in down_since:  # it just recovered
                        minutes = (time.time() - down_since.pop(name)) / 60
                        await send_email(client, f"[UP] {name} is back",
                                         f"{name} ({d['url']}) is back up after about {minutes:.0f} minute(s).")
                    failures[name] = 0
                    continue

                failures[name] += 1
                if failures[name] == FAILURE_THRESHOLD:  # alert once per outage
                    down_since[name] = time.time()
                    print(f"  Asking Gemini about {name}...")
                    report = await ai_report(d)
                    await send_email(
                        client, f"[DOWN] {name}",
                        f"{name} is DOWN\nURL: {d['url']}\nError: {d['error']}\n"
                        f"Time: {datetime.now():%Y-%m-%d %H:%M:%S}\n\n"
                        f"--- Report ---\n{report}",
                    )

            await asyncio.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")