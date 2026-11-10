"""W107.2 Part A/B: NBA injury-report news -> Kalshi KXNBAGAME price event study.  Read-only on all inputs.
usage: run_study.py PDF_DIR PRICE_ARCHIVE_DIR OUT_JSON"""
import glob, json, re, sys, collections
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "src")
from pypdf import PdfReader
from prediction_market_bot.quant import news_lag as nl

pdf_dir, arch_dir, out = sys.argv[1:4]
ET = ZoneInfo("America/New_York")
H = re.compile(r"Report:\s+(\d\d)/(\d\d)/(\d\d)\s+(\d\d):(\d\d)\s+(AM|PM)")
reports = []
for f in sorted(glob.glob(pdf_dir + "/*.pdf")):
    t = "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    m = H.search(t)
    if not m: continue
    mo, d, y, hh, mm, ap = m.groups()
    hh = int(hh) % 12 + (12 if ap == "PM" else 0)
    ts = datetime(2000 + int(y), int(mo), int(d), hh, int(mm), tzinfo=ET).astimezone(timezone.utc)
    reports.append((ts, nl.parse_injury_text(t)))
reports.sort(key=lambda r: r[0])
# dedupe identical header times
seen, rep = set(), []
for ts, rows in reports:
    if ts in seen: continue
    seen.add(ts); rep.append((ts, rows))
events = []
for (t0, r0), (t1, r1) in zip(rep, rep[1:]):
    events += nl.report_events(r0, r1, t1)

# price archive -> {(game_date_code, team_code): [(ts, yes_mid)]}
MON = {m: i for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split(), 1)}
px = collections.defaultdict(list)
for f in sorted(glob.glob(arch_dir + "/prices_2026-1*.jsonl")):
    for line in open(f):
        if '"KXNBAGAME"' not in line: continue
        r = json.loads(line)
        m = re.match(r"KXNBAGAME-26([A-Z]{3})(\d\d)([A-Z]+)-([A-Z]+)$", r["ticker"])
        if not m or r["status"] != "active": continue
        ts = datetime.strptime(r["run_ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        key = (f"2026-{MON[m.group(1)]:02d}-{m.group(2)}", m.group(3), m.group(4))
        if float(r["half_spread"]) > 0.10: continue          # unquoted / empty book
        px[key].append((ts, float(r["yes_mid"])))
for k in px: px[k].sort()
games = {(k[0], k[1]) for k in px}

def code(c):  # report code -> kalshi code (learned empirically below)
    return {"BKN": "BKN", "PHX": "PHX"}.get(c, c)

unmatched = collections.Counter()
def series_for(e):
    a, h = e.matchup.split("@")
    team = a if e.side == "away" else h
    pair = a + h
    for k in px:
        if k[0] == e.game_date and k[2] == team and k[1] in (pair,):
            return px[k]
    unmatched[e.matchup] += 1
    return None

KINDS = ["to_out", "to_questionable", "q_to_active", "out_to_active"]
res = {"reports": len(rep), "events": len(events), "games_priced": len(games),
       "report_span": [str(rep[0][0]), str(rep[-1][0])], "by_kind": {}}
hz = [20, 40, 60, 120]
for k in KINDS + ["ALL"]:
    ev = [e for e in events if k == "ALL" or e.kind == k]
    prof = nl.signed_profile(ev, series_for, hz)
    prof["increment_20_60"] = nl.increment(series_for, ev, 20, 60)
    res["by_kind"][k] = prof
res["unmatched_matchups_top"] = unmatched.most_common(8)
json.dump(res, open(out, "w"), indent=1, default=str)
print(json.dumps({k: {h: (v["n"], round(v.get("mean_signed", 0), 4)) for h, v in p["horizons"].items()} | {"pre": (p["pre"]["n"], round(p["pre"].get("mean_signed", 0), 4))} for k, p in res["by_kind"].items()}, indent=0))
print(res["reports"], res["events"], res["games_priced"], res["unmatched_matchups_top"])
