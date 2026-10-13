"""W70.1 NFL fill-timing audit (read-only). Input: JSON from scripts/demo_fill_timing_audit_collect.py
(run on the VPS:  python3 scripts/demo_fill_timing_audit_collect.py > nfl.json), path as argv[1]."""
import json,re,urllib.request
from datetime import datetime,timezone
from collections import Counter,defaultdict
d=json.load(open(__import__("sys").argv[1]))
def P(s):
    s=s.replace("Z","+00:00")
    m=re.match(r"(.*?\.)(\d+)(.*)",s)
    if m: s=m.group(1)+(m.group(2)+"000000")[:6]+m.group(3)
    elif s.endswith("+00:00") and "T" in s and s.count(":")<3: pass
    return datetime.fromisoformat(s)
ko={}
for day in ("20261008","20261009","20261010","20261011","20261012","20261013"):
    j=json.load(urllib.request.urlopen(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={day}"))
    for e in j["events"]:
        t=frozenset(c["team"]["abbreviation"] for c in e["competitions"][0]["competitors"])
        ko[t]=P(e["date"])
alias={'WAS':'WSH','JAC':'JAX'}
def kick(tk):
    seg=tk.split("-")[1][7:]
    for i in (2,3):
        x,y=seg[:i],seg[i:]
        if len(x)<2 or len(y)<2: continue
        for k,v in ko.items():
            if {alias.get(x,x),alias.get(y,y)}==set(k) or {x,y}==set(k): return v
rows=[];miss=Counter()
for r in d:
    k=kick(r["ticker"])
    if not k: miss[r["ticker"].split("-")[1]]+=1;continue
    r["ko"]=k;rows.append(r)
print("no kickoff match:",dict(miss))
print("orders created after kickoff:",sum(1 for r in rows if P(r["created"])>r["ko"]),"of",len(rows))
fl=[r for r in rows if float(r["fills"] or 0)>0]
fp=lambda r: float(r["yes_price"]) if r["side"]=="yes" else float(r["no_price"])
won=lambda r: r["result"]==r["side"]
def stat(rs,name):
    s=[r for r in rs if r.get("result") in("yes","no")]
    if not s: print(name,len(rs),"none settled");return
    print(f"{name}: fills={len(rs)} settled={len(s)} win={sum(map(won,s))/len(s):.3f} s-p={sum((1.0 if won(r) else 0.0)-fp(r) for r in s)/len(s):+.3f}")
pre=[];post=[]
for r in fl:
    r["ft"]=max(P(t) for t in r["fill_times"]) if r.get("fill_times") else P(r["last_update"])
    r["lag_min"]=(r["ft"]-r["ko"]).total_seconds()/60
    (post if r["ft"]>r["ko"] else pre).append(r)
stat(fl,"ALL");stat(pre,"fill BEFORE kickoff");stat(post,"fill AFTER kickoff")
print("have fill_times:",sum(1 for r in fl if r.get("fill_times")),"of",len(fl))
print("fill rel. kickoff, hour buckets:",sorted(Counter(int(r["lag_min"]//60) for r in fl).items()))
cr=sorted((P(r["created"])-r["ko"]).total_seconds()/3600 for r in fl);print("order created rel kickoff hrs min/med/max:",round(cr[0],1),round(cr[len(cr)//2],1),round(cr[-1],1))
print("status:",Counter(r["status"] for r in rows),"arms",Counter(r["arm"] for r in rows))
lag=sorted((r["ft"]-P(r["created"])).total_seconds() for r in fl);print("fill lag after order s p10/50/90/max:",round(lag[len(lag)//10]),round(lag[len(lag)//2]),round(lag[9*len(lag)//10]),round(lag[-1]))
g=defaultdict(list)
for r in fl:g[r["ticker"].split("-")[1]].append(r)
for k,v in sorted(g.items()):stat(v,"  "+k)
print("---- clustering")
c=Counter((r["ticker"],r["side"]) for r in fl);print("distinct ticker-sides among fills:",len(c),"; fills per (ticker,side):",sorted(c.values(),reverse=True)[:10])
u={}
for r in fl:u.setdefault((r["ticker"],r["side"]),r)
stat(list(u.values()),"first fill per ticker-side (independent positions)")
for k,r in sorted(u.items()):
    if r.get("result"): print("  ",k,"px",fp(r),"result",r["result"],"n_fills",c[k])
allc=Counter((r["ticker"],r["side"]) for r in rows);print("all orders distinct ticker-sides:",len(allc),"filled share of orders",len(fl)/len(rows))
