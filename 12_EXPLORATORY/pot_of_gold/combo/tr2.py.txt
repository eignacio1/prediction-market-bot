import json,statistics as st,datetime
ms=json.load(open("m_KXMVENBASINGLEGAME.json"))["markets"]
out=json.load(open("nba_trades.json"))
p=lambda s:datetime.datetime.strptime(s[:19],"%Y-%m-%dT%H:%M:%S")
print(len(ms),"markets in file; with trades",sum(1 for v in out.values() if v))
n=[len(v) for v in out.values() if v is not None];print("n q",st.quantiles(n,n=4) if len(n)>4 else n,"total",sum(n))
h=[(p(m["close_time"])-p(t["created_time"])).total_seconds()/3600 for m in ms for t in (out.get(m["ticker"]) or [])]
print(len(h),[round(q,2) for q in st.quantiles(h,n=10)])
print("<=2h",round(sum(x<=2 for x in h)/len(h),3),"<=0.5h",round(sum(x<=.5 for x in h)/len(h),3))
print(next(v for v in out.values() if v)[:1])
