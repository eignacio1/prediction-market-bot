"""Real-browser (headless Chromium) check of the web dashboard — T-621 / Wave 48.3.

Usage: python scripts/browser_check_dashboard.py [--base http://localhost:8050] [--out DIR] [--tag before]
Loads / and /project, records console errors, page errors, failed/4xx-5xx requests,
time to first data render, full-page screenshot, and a text dump. Writes report.json.
Requires `pip install playwright && playwright install chromium` (not a repo dependency).
"""
import argparse, json, os, pathlib, time
from playwright.sync_api import sync_playwright


def check(page, base, path, out, tag):
    rec = {"path": path, "console_errors": [], "page_errors": [], "failed_requests": [], "bad_status": []}
    page.on("console", lambda m: rec["console_errors"].append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: rec["page_errors"].append(str(e)))
    page.on("requestfailed", lambda r: rec["failed_requests"].append(f"{r.url} {r.failure}"))
    page.on("response", lambda r: rec["bad_status"].append(f"{r.status} {r.url}") if r.status >= 400 else None)
    t0 = time.time()
    page.goto(base + path, wait_until="domcontentloaded", timeout=60000)
    rec["t_domcontentloaded_s"] = round(time.time() - t0, 2)
    if path == "/":
        try:
            page.wait_for_function("document.getElementById('sha') && document.getElementById('sha').textContent.trim() !== '—'", timeout=60000)
            rec["t_first_data_render_s"] = round(time.time() - t0, 2)
        except Exception as e:
            rec["t_first_data_render_s"] = None
            rec["first_render_error"] = str(e)[:200]
    else:
        page.wait_for_load_state("load", timeout=60000)
        rec["t_first_data_render_s"] = round(time.time() - t0, 2)
    page.wait_for_timeout(1500)
    name = ("index" if path == "/" else path.strip("/")) + f".{tag}"
    page.screenshot(path=str(out / f"{name}.png"), full_page=True)
    rec["text"] = page.inner_text("body")[:20000]
    (out / f"{name}.txt").write_text(rec["text"])
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8050")
    ap.add_argument("--out", default="exp_output/w48_3_screens")
    ap.add_argument("--tag", default="before")
    a = ap.parse_args()
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    res = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None)
        for path in ("/", "/project"):
            ctx = b.new_context(viewport={"width": 1600, "height": 1000})
            res.append(check(ctx.new_page(), a.base, path, out, a.tag))
            ctx.close()
        b.close()
    (out / f"report.{a.tag}.json").write_text(json.dumps(res, indent=1))
    for r in res:
        print(r["path"], {k: v for k, v in r.items() if k != "text"})
