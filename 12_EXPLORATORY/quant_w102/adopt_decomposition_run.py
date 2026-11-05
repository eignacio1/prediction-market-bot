import json,sys
sys.path.insert(0,'/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20261105T060108Z-w102-4-quant/src')
from prediction_market_bot.quant.fill_decomposition import decompose,cluster_bootstrap
R=json.load(open('recs.json'))
f=[r for r in R if r['filled'] and r['settled']]
def run(name,key):
    rows=[(r['arm'],r['game'],key(r),r['w']-r['price']) for r in f]
    b=cluster_bootstrap(rows,reps=2000,seed=7)
    p=b['point']
    print('==',name,'games',b['games'])
    for k in('total','placement','selection','unmatched','skipped_control'):
        print(f"  {k:16s} {p[k]:+.4f}  90% [{b[k][0]:+.4f},{b[k][1]:+.4f}]")
    print('  nT',p['n_treatment'],'nC',p['n_control'],'common strata',p['n_common_strata'],'nT common',p.get('n_treatment_common'),'skipped C n',p.get('n_skipped_control'))
run('ticker+side',lambda r:(r['ticker'],r['side']))
run('ticker+side+hour',lambda r:(r['ticker'],r['side'],r['ts'][:13]))
run('ticker+side+day',lambda r:(r['ticker'],r['side'],r['ts'][:10]))
