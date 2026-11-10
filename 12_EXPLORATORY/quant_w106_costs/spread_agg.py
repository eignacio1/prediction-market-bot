"""W106.2 Part A2: realized half-spread per series x price band x days-before-game, streamed from PRICE_ARCHIVE.
Read-only. Run on the box: ssh box "cd /opt/prediction-market-bot && nice python3 -" < spread_agg.py   (prints JSON, <60 KB).
tts proxy = ticker date minus snapshot date (calendar days; game start time is not in the archive, see W103.2 INVENTORY)."""
import glob, json, re, sys, datetime as dt, collections
MON = {m: i + 1 for i, m in enumerate("JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split())}
RX = re.compile(r"-(\d{2})([A-Z]{3})(\d{2})")
BANDS = [(0.02, .10), (.10, .30), (.30, .50), (.50, .70), (.70, .90), (.90, .98)]
def band(m):
    for i, (a, b) in enumerate(BANDS):
        if a <= m < b: return i
def tts(ev, day):
    r = RX.search(ev or "")
    if not r or r.group(2) not in MON: return None
    d = dt.date(2000 + int(r.group(1)), MON[r.group(2)], int(r.group(3)))
    n = (d - day).days
    return "D0" if n <= 0 else "D1" if n == 1 else "D2+"
agg = collections.defaultdict(lambda: [0, 0.0, collections.Counter()])
files = sorted(glob.glob("exp_output/PRICE_ARCHIVE/prices_*.jsonl"))
for fp in files:
    day = dt.date.fromisoformat(fp.split("prices_")[1][:10])
    with open(fp) as fh:
        for line in fh:
            try: d = json.loads(line)
            except Exception: continue
            m, hs = d.get("yes_mid"), d.get("half_spread")
            if m is None or hs is None or not (0 <= hs <= 0.5): continue
            b = band(m)
            if b is None: continue
            t = tts(d.get("event_ticker"), day)
            if t is None: continue
            a = agg[(d["series_ticker"], b, t)]
            a[0] += 1; a[1] += hs; a[2][round(hs * 200)] += 1
out = []
for (s, b, t), (n, tot, h) in sorted(agg.items()):
    if n < 30: continue
    half, c, med = n / 2, 0, None
    for k in sorted(h):
        c += h[k]
        if c >= half: med = k / 200; break
    out.append([s, b, t, n, round(tot / n, 5), med])
print(json.dumps({"files": len(files), "bands": BANDS, "cols": "series,band,tts,n,mean_half_spread,median_half_spread", "rows": out}, separators=(",", ":")))
