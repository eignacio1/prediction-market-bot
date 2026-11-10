"""W108.2 / B-063: NBA injury-report news -> Kalshi trade-print price path (moneyline, spread, total).
Public GETs only, polite rate, cached per (ticker, window).  Writes only under 12_EXPLORATORY via safe_out.
usage: PYTHONPATH=12_EXPLORATORY python3 run_study_w108_2.py PDF_DIR TRADE_CACHE_DIR OUT_JSON"""
import collections, glob, hashlib, json, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
sys.path.insert(0, "src")
from _fence import safe_out
from pypdf import PdfReader
from prediction_market_bot.quant import news_lag as nl, trade_path as tp

pdf_dir, cache_dir, out = sys.argv[1:4]
ET, BASE = ZoneInfo("America/New_York"), "https://api.elections.kalshi.com/trade-api/v2"
H = re.compile(r"Report:\s+(\d\d)/(\d\d)/(\d\d)\s+(\d\d):(\d\d)\s+(AM|PM)")
MON = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
import os; os.makedirs(cache_dir, exist_ok=True)

def get_json(path, params):
    key = hashlib.md5((path + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    fp = os.path.join(cache_dir, key + ".json")
    if os.path.exists(fp):
        return json.load(open(fp))
    for attempt in range(4):
        try:
            r = urllib.request.urlopen(urllib.request.Request(BASE + path + "?" + urllib.parse.urlencode(params),
                                       headers={"User-Agent": "Mozilla/5.0"}), timeout=30)
            d = json.loads(r.read()); break
        except Exception as ex:
            time.sleep(2 * (attempt + 1)); d = None
    if d is None:
        return {"trades": [], "markets": [], "cursor": "", "_failed": True}
    json.dump(d, open(fp, "w")); time.sleep(0.2)
    return d

# ---- reports -> events (15-minute grid: the first report that shows a change carries its time) ----
reports, seen = [], set()
for f in sorted(glob.glob(pdf_dir + "/*.pdf")):
    try:
        t = "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    except Exception:
        continue
    m = H.search(t)
    if not m: continue
    mo, d, y, hh, mm, ap = m.groups()
    ts = datetime(2000 + int(y), int(mo), int(d), int(hh) % 12 + (12 if ap == "PM" else 0), int(mm), tzinfo=ET).astimezone(timezone.utc)
    if ts in seen: continue
    seen.add(ts); reports.append((ts, nl.parse_injury_text(t)))
reports.sort(key=lambda r: r[0])
events = []
for (t0, r0), (t1, r1) in zip(reports, reports[1:]):
    events += nl.report_events(r0, r1, t1)
# keep only news with >= 35 min of pre-tip market after it
events = [e for e in events if e.tip_utc - e.report_utc >= timedelta(minutes=35)]

# ---- tickers: market lists by game day, per series ----
series_mkts = collections.defaultdict(list)      # (series, event_ticker) -> [market]
days = sorted({e.game_date for e in events})
for s in ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL"):
    lo = datetime.fromisoformat(days[0]).replace(tzinfo=timezone.utc) - timedelta(days=1)
    hi = datetime.fromisoformat(days[-1]).replace(tzinfo=timezone.utc) + timedelta(days=3)
    cur = None
    while True:
        p = {"series_ticker": s, "min_close_ts": int(lo.timestamp()), "max_close_ts": int(hi.timestamp()), "limit": 1000}
        if cur: p["cursor"] = cur
        d = get_json("/markets", p)
        for m in d.get("markets", []): series_mkts[(s, m["event_ticker"])].append(m)
        cur = d.get("cursor")
        if not cur: break

def event_ticker(series, e):
    a, h = e.matchup.split("@")
    y, mo, dd = e.game_date.split("-")
    return f"{series}-{y[2:]}{MON[int(mo)-1]}{dd}{a}{h}"

def pick(series, e):
    ms = series_mkts.get((series, event_ticker(series, e)), [])
    if series == "KXNBAGAME":
        a, h = e.matchup.split("@"); team = a if e.side == "away" else h
        c = [m for m in ms if m["ticker"].endswith("-" + team)]
    elif series == "KXNBASPREAD":
        a, h = e.matchup.split("@"); team = a if e.side == "away" else h
        c = [m for m in ms if re.match(rf".*-{team}\d+$", m["ticker"])]
    else:
        c = ms
    return max(c, key=lambda m: float(m.get("volume_fp") or 0))["ticker"] if c else None

MINS = [-1, 0, 1, 2, 3, 5, 10, 20, 30]
res = {"reports": len(reports), "events": len(events), "families": {}}
unmatched = collections.Counter()
for fam in ("KXNBAGAME", "KXNBASPREAD", "KXNBATOTAL"):
    rows = []
    for e in events:
        tk = pick(fam, e)
        if not tk:
            unmatched[(fam, e.matchup)] += 1; continue
        t0 = e.report_utc
        raw = tp.fetch_trades(get_json, tk, t0 - timedelta(hours=3), t0 + timedelta(minutes=31), pause=0.2)
        tr = tp.parse_trades(raw)
        # placebo: same market, news time shifted 2h earlier (no news), same tests below
        for tag, T0 in (("news", t0), ("placebo", t0 - timedelta(hours=2))):
            sg = e.sign if fam != "KXNBATOTAL" else +1
            sp = tp.signed_path(tr, T0, sg, MINS)
            fin_lvl = tp.tail_level(tr, T0, 20, 30)
            if not sp or fin_lvl is None: continue
            rows.append({"tag": tag, "game": e.matchup + e.game_date, "kind": e.kind, "sign": e.sign, "ticker": tk,
                         "ref": sp["ref"], "ref_age_s": sp["ref_age_s"], "path": sp["path"], "final": sg * (fin_lvl - sp["ref"]),
                         "n_prints_0_30": sum(1 for x in tr if T0 < x.ts <= T0 + timedelta(minutes=30)),
                         "lag50": tp.lag_to_fraction(tr, T0, sg, 0.5, sg * (fin_lvl - sp["ref"])),
                         "lag100": tp.lag_to_fraction(tr, T0, sg, 1.0, sg * (fin_lvl - sp["ref"])),
                         "pre": (lambda q: None if not q or q["path"][25] is None or q["path"][30] is None else
                                 {"m30_m5": q["path"][25], "m5_0": q["path"][30] - q["path"][25]})(tp.signed_path(tr, T0 - timedelta(minutes=30), sg, [25, 30])),
                         "entry": {k: tp.entry_net(tr, T0, sg, k, fin_lvl, fam) for k in (1, 2, 5)} if fam != "KXNBATOTAL" else None})
    res["families"][fam] = rows
res["unmatched_top"] = unmatched.most_common(10)
json.dump(res, open(safe_out(out), "w"), default=str)
print({f: len([r for r in v if r["tag"] == "news"]) for f, v in res["families"].items()}, res["events"], res["reports"])
