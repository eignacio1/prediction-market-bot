import json,collections,statistics as st
ms=json.load(open("mve_open_all.json"))["markets"]
f=lambda x,k:float(x.get(k) or 0)
def state(x):
    b,a=f(x,"yes_bid_dollars"),f(x,"yes_ask_dollars")
    return ("bid" if b>0 else "-")+("ask" if a<1 else "-")
print(collections.Counter(state(x) for x in ms))
ask=[x for x in ms if f(x,"yes_ask_dollars")<1]
print("ask dist deciles",[round(q,3) for q in st.quantiles([f(x,'yes_ask_dollars') for x in ask],n=10)])
print("ask size q",[round(q) for q in st.quantiles([f(x,'yes_ask_size_fp') for x in ask],n=4)])
bidx=[x for x in ms if f(x,"yes_bid_dollars")>0];print("bid>0",len(bidx),[round(q,4) for q in st.quantiles([f(x,'yes_bid_dollars') for x in bidx],n=4)])
c=collections.defaultdict(lambda:[0,0])
for x in ms:
    n=min(len(x["mve_selected_legs"]),8);c[n][0]+=1;c[n][1]+=f(x,"yes_ask_dollars")<1
print({k:(v[0],round(v[1]/v[0],2)) for k,v in sorted(c.items())})
sg=[x for x in ms if all(l["event_ticker"].startswith("KXNBA") for l in x["mve_selected_legs"]) and len({l["event_ticker"].split("-",1)[1] for l in x["mve_selected_legs"]})==1]
print("single-game NBA:",len(sg),"with ask",sum(f(x,'yes_ask_dollars')<1 for x in sg),"traded",sum(f(x,'volume_fp')>0 for x in sg),"legs",collections.Counter(len(x['mve_selected_legs']) for x in sg).most_common(6))
print("leg families sg:",collections.Counter(l["event_ticker"].split("-")[0] for x in sg for l in x["mve_selected_legs"]))
tr=[x for x in ms if f(x,"volume_fp")>0];print("traded legs dist",collections.Counter(len(x['mve_selected_legs']) for x in tr).most_common(5))
x=ask[0];print({k:x[k] for k in("yes_bid_dollars","yes_ask_dollars","yes_ask_size_fp","no_bid_dollars","no_ask_dollars","last_price_dollars","volume_fp")})
print([ (x['last_price_dollars'],x['yes_ask_dollars']) for x in ask if f(x,'last_price_dollars')>0][:6])
