import json,collections,statistics as st
ms=json.load(open("mve_open_all.json"))["markets"]
f=lambda x,k:float(x.get(k) or 0)
hb=lambda x:f(x,"yes_bid_dollars")>0 and f(x,"yes_bid_size_fp")>0
ha=lambda x:0<f(x,"yes_ask_dollars")<1 and f(x,"yes_ask_size_fp")>0
S=collections.Counter(("bid" if hb(x) else "-")+("ask" if ha(x) else "-") for x in ms);print(S)
sg=[x for x in ms if all(l["event_ticker"].startswith("KXNBA") for l in x["mve_selected_legs"]) and len({l["event_ticker"].split("-",1)[1] for l in x["mve_selected_legs"]})==1]
print("sg NBA",len(sg),collections.Counter(("bid" if hb(x) else "-")+("ask" if ha(x) else "-") for x in sg))
for nm,grp in(("all",ms),("sgNBA",sg)):
    A=[f(x,"yes_ask_dollars") for x in grp if ha(x)];B=[f(x,"yes_bid_dollars") for x in grp if hb(x)]
    print(nm,"ask n",len(A),"q",[round(q,3) for q in st.quantiles(A,n=4)] if len(A)>4 else A,"| bid n",len(B),"q",[round(q,4) for q in st.quantiles(B,n=4)] if len(B)>4 else B)
    print("  ask size q",[round(q) for q in st.quantiles([f(x,'yes_ask_size_fp') for x in grp if ha(x)],n=4)] if A else "")
both=[x for x in ms if hb(x) and ha(x)]
for x in both:print("two-sided",len(x["mve_selected_legs"]),x["yes_bid_dollars"],x["yes_ask_dollars"],x["last_price_dollars"],x["volume_fp"])
tr=[x for x in ms if f(x,"volume_fp")>0]
print("traded",len(tr),"of which ask now",sum(ha(x) for x in tr),"sum vol",round(sum(f(x,'volume_fp') for x in tr)))
# time-to-close of quoted sgNBA
import datetime
t0=datetime.datetime(2026,11,25,0,27,45)
def hrs(x):return (datetime.datetime.strptime(x["close_time"],"%Y-%m-%dT%H:%M:%SZ")-t0).total_seconds()/3600
print("sgNBA close hrs quantiles",[round(q,1) for q in st.quantiles([hrs(x) for x in sg],n=4)])
print("last_price vs ask for traded+ask:",sorted([(x['last_price_dollars'],x['yes_ask_dollars'],x['yes_bid_dollars']) for x in tr if ha(x)][:8]))
