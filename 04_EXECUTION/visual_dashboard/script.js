/* ============================================================ DATA (edited by the strategic window at each wave close) */
const DIST = [
  ["Breadth","B1","Cells logging / registered","40 / 107","the whole board","0 — 10-21 flip rehearsed, frozen NBA book locked (71.2)"],
  ["Breadth","B2","Families with a logging cell","13 / 18","18 / 18, props + parlays registered","0"],
  ["Breadth","B3","Bands with a logging cell","4 of 5 (no T5)","5 of 5, T4 sub-bands","0"],
  ["Breadth","B4","Props · parlay families logging","2 · 0","the board's props and parlays","0"],
  ["Depth","D1","Factor classes per pre-game model","NFL team + personnel (QB challenger live); NBA points minutes + injury accepted, not yet logging; nobody uses matchup, weather, qualitative","every class at every arm","0 — availability on NBA games: NO (71.3)"],
  ["Depth","D2","Largest pre-game feature set","18 (MLB hits, 0 qualitative)","coverage of classes, not a count","0"],
  ["Depth","D3","Pre-registered challengers ready","2 (NFL QB-shrunk, live · NBA points EXP-040, frozen)","≥ 1 per arm before its first look","0 — EXP-040 deployed, 0 rows until NBA points markets list"],
  ["Execution","E1","Demo orders filled","T4 166 / 4,237 · T1 85 / 485","fills ≈ intended orders","since re-arm: 0 cancel failures; fills 0/1/3/1/1 per arm, none settled yet"],
  ["Execution","E2","P&L per filled bet","T4 −$0.26 · T1 −$1.50","positive, net of fees","NFL +0.398 audited: before kickoff, but ~4 correlated games — not evidence"],
  ["Execution","E3","Win rate, fills vs non-fills","T4 24.1% vs 48.7% · T1 28.9% vs 52.1%","fills at least as good","0 — first settled numbers in 73.1"],
  ["Proof","P1","Cells at a scored look","0 / 45","every cell judged at its n","0"],
  ["Proof","P2","Verdicts issued","0","a verdict per cell (a NO counts)","0"],
  ["Proof","P3","Next look","NFL ~11-02 · ~91% \"keep accruing\"","—","—"],
];

const F = [
  {g:"vs the market — the question that matters",
   rows:[
    {l:"EXP-029 · MLB pre-game model vs Kalshi KXMLBHIT", s:"215 games · 1,316 rows · frozen model, scored once",
     m:-0.00393, lo:-0.00629, hi:-0.00152, v:"HARMFUL", c:"crit"},
    {l:"W61.3 · NFL frozen model vs Kalshi mid, 2025", s:"182 games · exploratory, not a pre-registered verdict",
     m:-0.0068, lo:-0.0227, hi:0.0094, v:"NO DETECTABLE DIFF", c:"warn"},
   ]},
  {g:"vs an incumbent model",
   rows:[
    {l:"W64.1 · NFL QB-shrunk challenger vs frozen, 2019–2025", s:"1,852 games · 6 of 7 seasons better · 99.375% CI",
     m:0.0027, lo:0.0006, hi:0.0050, v:"IMPROVEMENT (backtest)", c:"good"},
    {l:"W64.1 · same challenger, 2025 priced games only", s:"182 games · the one season it was worse",
     m:-0.0039, lo:-0.0115, hi:0.0031, v:"NO DETECTABLE DIFF", c:"warn"},
    {l:"W69.3 · NBA points ≥15, minutes + injury vs EXP-039 model", s:"backtest · strike 15 only (worse at 25) · injury coverage 34% Jan–Apr",
     m:0.00047, lo:0.00015, hi:0.00079, v:"IMPROVEMENT (backtest)", c:"good"},
    {l:"W61.3 · NFL recalibration challenger vs frozen", s:"rolling origin · sign marginally worse",
     m:-0.00114, lo:-0.00254, hi:0.00022, v:"NO IMPROVEMENT", c:"warn"},
    {l:"EXP-030 · T4 structural tree vs 3-scalar binomial", s:"40 of 40 test games differed · power floor met",
     m:-0.0063, lo:-0.0203, hi:0.0091, v:"NO DETECTABLE DIFF", c:"warn"},
    {l:"EXP-028 · MLB pre-game tree vs shrunk-BA one-liner", s:"1,414 games · 27,732 rows",
     m:0.00364, lo:0.00293, hi:0.00435, v:"IMPROVEMENT", c:"good"},
    {l:"ADR-0066 · NFL EPA splits vs base adapter", s:"every interval spans zero",
     m:-0.0007, lo:-0.0042, hi:0.0028, v:"NO DETECTABLE DIFF", c:"warn"},
   ]},
  {g:"vs climatology — the low bar",
   rows:[
    {l:"EXP-028 · MLB pre-game tree vs climatology", s:"1,414 games · Δlog-loss +0.01065",
     m:0.00520, lo:0.00438, hi:0.00601, v:"DEFENSIBLE", c:"good"},
   ]},
  {g:"controls — these should contain zero",
   rows:[
    {l:"EXP-029 · permutation null", s:"contains 0 under both literal and one-sided rules",
     m:-0.000045, lo:-0.000133, hi:0.000044, v:"CONTROL OK", c:"good"},
    {l:"EXP-029 · backward placebo vs forward", s:"backward +0.00494 against forward +0.00484 · ratio 1.02",
     m:0.00494, lo:0.00400, hi:0.00588, v:"TIME-SYMMETRIC", c:"crit"},
   ]},
];

const MARKETS = [
  ["MLB_PLAYER_PROP_HITS","MLB player hits"],["MLB_MONEYLINE","MLB moneyline"],["MLB_RUN_LINE","MLB run line"],
  ["MLB_GAME_TOTAL","MLB game total"],["MLB_TEAM_TOTAL","MLB team total"],["MLB_PARTIAL_GAME","MLB partial game"],
  ["NFL_MONEYLINE","NFL moneyline"],["NFL_SPREAD","NFL spread"],["NFL_GAME_TOTAL","NFL game total"],["NFL_TEAM_TOTAL","NFL team total"],
  ["NHL_MONEYLINE","NHL moneyline"],["NHL_PUCK_LINE","NHL puck line"],["NHL_GAME_TOTAL","NHL game total"],
  ["NBA_MONEYLINE","NBA moneyline"],["NBA_SPREAD","NBA spread"],["NBA_GAME_TOTAL","NBA game total"],["NBA_TEAM_TOTAL","NBA team total"],
  ["NBA_PLAYER_POINTS","NBA player points"],
];
const BANDS = ["T1","T2","T3","T4","T4M-PROJ","T4M-ARITH","T4M-FLOW","T4NFL-ARITH","T4NFL-FLOW","T4NHL-ARITH","T4NHL-FLOW","T5"];
const CELLS = __CELLS__;
const MXNOTE = {
  "MLB_PLAYER_PROP_HITS|T4M-PROJ":"The only ACTIVE cell. Flat demo stakes; real fills −$0.26 a bet; stakes stop after the World Series (GG-527 c). Fails C5 (GG-320).",
  "MLB_PLAYER_PROP_HITS|T1":"18-feature LR + Platt, daily 11:00 UTC. Paper rows are calibration only (GG-536).",
  "NBA_PLAYER_POINTS|T4":"T4 is DARK (legacy NBA book, frozen). T1–T3 are SHADOW cells (EXP-039, frozen NB+Platt artifact), logging only.",
};

const ARMS = [
  ["NFL game markets",12,"Logging","good","EXP-037","~2026-11-02","15 of 60 games per cell; first look most likely \"keep accruing\""],
  ["NFL QB-shrunk challenger",2,"Logging","good","accepted 10-10","with EXP-037 vs the market","Moneyline; first live NFL model that knows who plays (since 10-11)"],
  ["MLB postseason game markets",12,"Logging","good","EXP-037 MLB","2027 regular season","Postseason rows logged, not scored"],
  ["MLB player hits T1–T3",3,"Logging","good","—","—","Stops with the World Series"],
  ["MLB player hits T4M-PROJ",1,"Active · demo stakes","good","ADR-0050","—","Stakes stop for every game after the World Series"],
  ["NHL game markets",9,"Logging","good","EXP-036","preliminary all 2026-27","Judged sample not reachable this season (GG-514)"],
  ["NBA game markets",12,"Preseason","warn","EXP-038","150 games per cell","Regular season from 10-20; cells flip ~10-21"],
  ["NBA player points T1–T3",3,"Logging","good","EXP-039","after opening night","Live since 10-11 (67.1); regular-season rows from 10-20"],
  ["NBA player points ≥15 + minutes/injury",1,"Logging","good","EXP-040","n=300 player-games","Wired 70.2: shadow, beside EXP-039; rows from first KXNBAPTS board; GG-610 caveat"],
];
const CAL = [
  ["10-12 00:00Z","First fill-fix forward-test orders (MLB game); 67.2 reads day one"],
  ["Mon 10-12","Weekly T4 ledger rebuild — first live test of the overwrite guard"],
  ["Thu 10-15","First NFL slate the QB challenger logs; first NFL injury snapshot due (66.3)"],
  ["Tue 10-20","NBA opening night — NBA game and player-points arms must be logging"],
  ["~11-02","NFL first scored look, 12 cells — the project's first pre-registered market verdict"],
  ["World Series end","T4M-PROJ stakes stop; MLB player hits stops producing rows; MLB winter posture is your call"],
  ["before 2027-01-31","Define what EXP-038's date-triggered NBA second look scores (GG-529)"],
];

const WAVES = [
  {w:"29–42", k:"neg", t:"Instruments built; both standing hypotheses negative.",
   d:"Pre-registration, a game-clustered A/B harness and a fail-closed evidence predicate. Then the tests: <b>EXP-029 HARMFUL</b> — the MLB pre-game model loses to the market — and <b>EXP-030</b>: a deeper in-play tree is indistinguishable from the 3-scalar one."},
  {w:"43–48", k:"hit", t:"From one cell to a board.",
   d:"The NHL arm becomes the first new arm flying (47.3). NFL and MLB postseason game markets — 24 cells — built and pre-registered (47.2). Candle reconstruction passes Gate 2 7/7 on KXMLBTOTAL. Blocks ran ~2 h, so block-size rules were introduced."},
  {w:"49–52", k:"", t:"Landing, and the kill-switch truth.",
   d:"Shadow code landed and auto-deployed. The dashboard's 26.6% drawdown was 10.6% realized plus stake on settled-but-unbooked positions (GG-441/450). NHL team codes silently dropped — fixed."},
  {w:"53–55", k:"hit", t:"Truthful books.",
   d:"<b>Kalshi settlement becomes the resolution source</b> (ADR-0071). 26 stuck positions booked. 24 SHADOW cells live. Nightly out-of-memory crashes traced (GG-477) and staggered away."},
  {w:"56–57", k:"", t:"Off statsapi; dashboards that tell the truth.",
   d:"MLB schedule, cache and features move to GitHub Actions. Live Terminal shows what the bot places now; the Visual Dashboard gets ops health, books and evidence clocks."},
  {w:"58–60", k:"neg", t:"One calibration engine — and the T4 cohort is mostly fiction.",
   d:"Every cell under its own pre-registration, sealed below judged n. NBA arm built (EXP-038). 1,229 / 1,229 settlements agree. Gap log 176 → 130. <b>94.5% of T4M-PROJ's rows never filled; real fills lose $0.40 a bet</b> (GG-527)."},
  {w:"61", k:"", t:"Fills-only counting.",
   d:"T4M-PROJ counted on real fills (n=165, ≈ −$0.26 a bet); stand-down gate for after the World Series; first-look release path fixed; the MLB postseason arm found silent (GG-532)."},
  {w:"62", k:"neg", t:"T1 has the same disease.",
   d:"<b>T1 MLB: 85 of 485 orders filled, fills −$1.50 a bet</b>, win 28.9% vs 52.1% for non-fills (GG-536). NFL first look written down in advance: ~91% \"keep accruing\". Silent-arm alarm live."},
  {w:"63", k:"hit", t:"The board +12, and why fills lose.",
   d:"MLB game-market cells SHADOW: <b>B1 25 → 37, B2 8 → 12</b>. Distance-to-optimum generated from data. <b>Fills are adversely selected</b>: orders rest 40–100 min at the model's price and fill when the market moves against them."},
  {w:"64", k:"hit", t:"The first depth challenger; the fix built.",
   d:"NFL QB-shrunk challenger beats frozen in backtest (<b>D3 0 → 1</b>) — but not the market. Fill fix (cancel after 60 s, price off the book) built OFF and pre-registered. NBA player points pre-registered; wiring carried. You accepted all three 10-10."},
  {w:"65", k:"neg", t:"NFL learns who plays; every demo order 404s.",
   d:"The NFL QB challenger is live in shadow (<b>D1: NFL team → team + personnel</b>). The forward test found <b>every demo order write returning 404</b> — the bot cannot place a demo order (GG-560). NBA points built in PR #217 but never merged. Breadth and Execution: three waves without a move."},
  {w:"66", k:"hit", t:"Demo orders were never down; the forward test is ON.",
   d:"The 404s were tickers the demo venue doesn't list (18 of 55 for one game) — and the canary had picked production tickers. Fixed; canary placed and cancelled; <b>ADR-0072 ACCEPTED, forward test ON</b>. MLB build 22.5 → 17.5 min. NBA points still on a branch: Breadth unmoved four waves."},
  {w:"67", k:"hit", t:"Breadth moves; shadow cells trade; GitHub cuts us off.",
   d:"<b>NBA player points live: B1 37/104 → 40/107, B4 1 → 2</b>. First accepted shadow-cell demo orders (36 in an hour). NFL injury reports captured before kickoff. Then GitHub refused all jobs — free minutes gone; repo made public, MLB data re-dispatched."},
  {w:"68", k:"neg", t:"MLB data back; nothing proven running.",
   d:"MLB feeds green on the public repo; CI restored. NBA + NHL stakes and a daily forward-test report merged — but the ssh read of the VPS was refused, so nothing verified running. NFL weather: <b>no arm beats frozen</b>."},
  {w:"69", k:"hit", t:"The forward test speaks; NBA opening night automated.",
   d:"First on-box forward-test numbers: <b>NFL shadow 231 fills of 1,135, +0.39 a fill</b> (too good — audited in 70); MLB shadow −0.20. NBA cells flip themselves from 10-21. NBA points challenger EXP-040 accepted + frozen (<b>D3 1 → 2</b>). Then the test switched itself off on a miscounted cancel (GG-596)."},
  {w:"70", k:"neg", t:"The good number didn't survive; the test stays off.",
   d:"NFL +0.39 a fill: real, before kickoff — but ~4 games that settle together, so <b>not evidence</b>. 8 real MLB-HIT cancel failures keep the whole forward test off (GG-623). EXP-040 deployed, waiting for markets. Main green. <b>No measure moved.</b>"},
  {w:"71", k:"neg", t:"Forward test back on; second wave without a measure.",
   d:"Cancels were going to the wrong exchange shard — fixed, <b>forward test ON</b>. NBA 10-20 rehearsed; frozen book locked. Who-is-out on NBA games: <b>NO</b>. Hygiene audit: <b>SOUND WITH ISSUES</b> (18 gaps; /vps dangerous; paper ledger not crash-safe). <b>No measure moved — two waves running.</b>"},
  {w:"72", k:"hit", t:"The foundation, fixed.",
   d:"Crash-safe ledgers; deploys prove the running code; the order path itself refuses real money; /vps retired; box secrets locked. Forward test live with both arms, <b>0 cancel failures</b>. No look-ahead found. You amended the turn-off and staked NBA."},
  {w:"73", k:"now", t:"The NFL engine starts.",
   d:"Syndicate32's factor list rebuilt from free data into an event-level store; one game simulation pricing moneyline, spread and total (<b>D4</b>). First settled forward-test numbers; NBA staked from opening night (E)."},
];

const DESK = [
  {a:"var(--serious)", t:"MLB winter posture", c:"After the World Series",
   d:"T4M-PROJ's stakes already stop by your GG-527 decision. <b>T1 MLB: stand down or idle all winter?</b> Until decided, Step 4 raises daily false alarms once games end."},
  {a:"var(--warn)", t:"NBA second look (GG-529)", c:"Before 2027-01-31",
   d:"EXP-038 says \"n = 400 or 31 Jan, whichever first\" but never says what is scored on the date. Needs a definition before January."},
  {a:"var(--warn)", t:"The efficiency-gradient call", c:"Open since 08-12",
   d:"Expand into efficient game markets accepting thinner edge as the price of generality, or hold expansion to looser markets? Every pre-registration already writes \"thinner edge expected\"."},
  {a:"var(--s1)", t:"ADR-0068 band doctrine · ADR-0067 append-only log", c:"PROPOSED",
   d:"The doctrine is enforced by a criterion not yet accepted. ADR-0067 changes what the evidence pool <i>is</i>; it matters only once order volume rises."},
  {a:"var(--s1)", t:"NBA model class (EXP-038 / EXP-039)", c:"Not blocking",
   d:"Both NBA arms run frozen models with no ADR for their model class. They log as shadow either way."},
  {a:"var(--ink-3)", t:"T1 MLB postseason flag", c:"Edits an existing cron line",
   d:"Adds <span class='mono'>--include-postseason</span> to the T1 MLB line. The shadow authorization does not cover editing a line."},
  {a:"var(--ink-3)", t:"GG-347 — the SSH poller", c:"Unexplained actor",
   d:"Something at 73.231.159.158 polls the VPS over SSH. Yours?"},
  {a:"var(--ink-3)", t:"EXP-034 · detached VPS jobs", c:"Park recommended",
   d:"EXP-034's ≥2.5-hour sampler: run it as a detached read-only VPS job, or park it."},
];

const GOV = __GOV__;
const SEV = [["CRITICAL","var(--crit)"],["HIGH","var(--serious)"],["MEDIUM","var(--warn)"],["LOW","var(--s1)"],
             ["UNSPECIFIED","var(--ink-3)"]].map(([k,c])=>[k,GOV.sev[k]||0,c]);
const ASYM = [["Registered, ever",GOV.ever,"var(--s2)"],["Retired to archive",GOV.retired,"var(--s3)"],
              ["Live",GOV.live,"var(--s1)"],["Live and OPEN",GOV.open,"var(--warn)"]];
/* ADR-0074 — process integrity: runtime registry + window error log, injected at build time */
const RUNTIME = __RUNTIME__;
const LIVE = __LIVE__;
const WINERR = __WINERR__;
const GAGENT = __GAGENT__;
const MUSEWEB = __MUSEWEB__;
const BACKLOG = __BACKLOG__;
const PICKS = __PICKS__;
const FUNNEL = [["T4 · closed",4237,"var(--seq-250)"],["T4 · filled",166,"var(--crit)"],
                ["T1 · closed",485,"var(--seq-250)"],["T1 · filled",85,"var(--crit)"]];

/* ============================================================ RENDER */
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
const tt=$('#tt');
function showTip(e,html){tt.innerHTML=html; tt.style.opacity='1';
  const r=tt.getBoundingClientRect(); let x=e.clientX+14,y=e.clientY+14;
  if(x+r.width>innerWidth-12)x=e.clientX-r.width-14;
  if(y+r.height>innerHeight-12)y=e.clientY-r.height-14;
  tt.style.left=x+'px'; tt.style.top=y+'px';}
function hideTip(){tt.style.opacity='0'}

function distance(){
  const PC={Breadth:'info',Depth:'warn',Execution:'crit',Proof:'mute'};
  $('#distBody').innerHTML=DIST.map(([p,c,m,now,opt,mv])=>{
    const moved=/^\+/.test(mv)?'good':(/accepted|ON in|live in/.test(mv)?'info':'mute');
    return `<tr><td><span class="chip ${PC[p]}"><i></i>${p}</span></td><td><span class="mono" style="color:var(--ink-3)">${c}</span> ${esc(m)}</td>`+
      `<td class="nowc">${esc(now)}</td><td style="color:var(--ink-3)">${esc(opt)}</td><td><span class="chip ${moved}"><i></i>${esc(mv)}</span></td></tr>`;
  }).join('');
}

function forest(){
  const all=F.flatMap(g=>g.rows);
  $('#verdCount').textContent=all.length+' measured effects'; $('#nvVerd').textContent=all.length;
  const lo=Math.min(...all.map(r=>r.lo)), hi=Math.max(...all.map(r=>r.hi));
  const pad=(hi-lo)*0.14, dmin=Math.min(lo-pad,-0.001), dmax=Math.max(hi+pad,0.001);
  const L=392, R=96, W=1000, rowH=42, headH=30;
  let n=0; F.forEach(g=>n+=g.rows.length+1);
  const H=n*rowH+headH+18;
  const x=v=>L+(v-dmin)/(dmax-dmin)*(W-L-R);
  const SC={crit:'var(--crit)',warn:'var(--warn)',good:'var(--good)',serious:'var(--serious)'};
  let s=`<svg class="forest" viewBox="0 0 ${W} ${H}" role="img" aria-label="Measured effects with intervals">`;
  const raw=(dmax-dmin)/6, mag=Math.pow(10,Math.floor(Math.log10(raw)));
  const step=[1,2,2.5,5,10].map(m=>m*mag).find(c=>c>=raw) || 10*mag;
  const ticks=[];
  for(let v=Math.ceil(dmin/step)*step; v<=dmax+1e-12; v+=step){ if(Math.abs(v)>step/4) ticks.push(v); }
  ticks.forEach(v=>{ s+=`<line class="fgrid" x1="${x(v).toFixed(1)}" y1="${headH-8}" x2="${x(v).toFixed(1)}" y2="${H-18}"/>`;
    s+=`<text class="ftick" x="${x(v).toFixed(1)}" y="${headH-14}" text-anchor="middle">${v>0?'+':''}${v.toFixed(3)}</text>`;});
  s+=`<text class="ftick" x="${x(0).toFixed(1)}" y="${headH-14}" text-anchor="middle" style="fill:var(--ink-2);font-weight:700">0</text>`;
  s+=`<line class="fz" x1="${x(0).toFixed(1)}" y1="${headH-8}" x2="${x(0).toFixed(1)}" y2="${H-18}"/>`;
  s+=`<text class="fsub" x="${x(0).toFixed(1)}" y="${H-5}" text-anchor="middle">no difference</text>`;
  s+=`<text class="fsub" x="${L}" y="${H-5}">← market / incumbent better</text>`;
  s+=`<text class="fsub" x="${W-R}" y="${H-5}" text-anchor="end">candidate better →</text>`;
  let y=headH+16;
  F.forEach(g=>{
    s+=`<text class="fsub" x="8" y="${y+4}" style="font-weight:700; letter-spacing:.06em; text-transform:uppercase; font-size:9.4px">${esc(g.g)}</text>`;
    y+=rowH*0.62;
    g.rows.forEach(r=>{
      const col=SC[r.c]||'var(--s1)';
      s+=`<g class="frow" data-tip="${encodeURIComponent(
          `<div class="h">${r.l}</div><div style="font-size:11.4px;color:var(--ink-3);margin-bottom:6px">${r.s}</div>`+
          `<div class="r"><span>ΔBrier</span><b>${r.m>0?'+':''}${r.m.toFixed(5)}</b></div>`+
          `<div class="r"><span>interval</span><b>[${r.lo.toFixed(5)}, ${r.hi.toFixed(5)}]</b></div>`+
          `<div class="r"><span>verdict</span><b>${r.v}</b></div>`)}">`;
      s+=`<rect class="fbg" x="0" y="${y-15}" width="${W}" height="${rowH-8}" fill="transparent" rx="5"/>`;
      s+=`<text class="flabel" x="8" y="${y-1}">${esc(r.l)}</text>`;
      s+=`<text class="fsub" x="8" y="${y+12}">${esc(r.s)}</text>`;
      s+=`<line class="fci" x1="${x(r.lo).toFixed(1)}" y1="${y+1}" x2="${x(r.hi).toFixed(1)}" y2="${y+1}" stroke="${col}"/>`;
      s+=`<circle class="fpt" cx="${x(r.m).toFixed(1)}" cy="${y+1}" r="4.6" fill="${col}"/>`;
      const right=x(r.hi)+9+r.v.length*6.2 < W-4;
      const lx=right? x(r.hi)+9 : x(r.lo)-9, anc=right?'start':'end';
      s+=`<text class="fsub" x="${lx.toFixed(1)}" y="${y+5}" text-anchor="${anc}" style="font-family:var(--mono);font-size:9.6px;fill:${col};font-weight:700">${r.v}</text>`;
      s+=`</g>`;
      y+=rowH;
    });
    y+=6;
  });
  s+=`</svg>`;
  $('#forestWrap').innerHTML=s;
  $$('#forestWrap .frow').forEach(g=>{
    g.addEventListener('mousemove',e=>showTip(e,decodeURIComponent(g.dataset.tip)));
    g.addEventListener('mouseleave',hideTip);
  });
  let t=`<div class="tscroll"><table><thead><tr><th>Test</th><th>Measured against</th><th class="num">ΔBrier</th><th class="num">Interval</th><th>Verdict</th></tr></thead><tbody>`;
  F.forEach(g=>g.rows.forEach(r=>{
    t+=`<tr><td class="k">${esc(r.l)}<div style="font-size:11px;color:var(--ink-3);font-weight:400">${esc(r.s)}</div></td>`+
       `<td>${esc(g.g)}</td><td class="num">${r.m>0?'+':''}${r.m.toFixed(5)}</td>`+
       `<td class="num">[${r.lo.toFixed(5)}, ${r.hi.toFixed(5)}]</td>`+
       `<td><span class="chip ${r.c}"><i></i>${esc(r.v)}</span></td></tr>`;
  }));
  $('#forestTable').innerHTML=t+`</tbody></table></div>`;
}

function bars(host,data){
  const max=Math.max(...data.map(d=>d[1]));
  $(host).innerHTML=data.map(([l,v,c])=>
    `<div class="bar"><div class="bl">${l}</div><div class="bt">`+
    `<div class="bf" style="width:${Math.max(v/max*100,v?1.2:0).toFixed(1)}%;background:${c}"></div></div>`+
    `<div class="bv">${v.toLocaleString()}</div></div>`).join('');
}

const SLABEL={wins:"WINS — pre-registered positive verdict at judged n",active:"ACTIVE — staked, no winning verdict",shadow:"SHADOW — evaluates and logs",not_implemented:"Defined, not implemented",blocked:"BLOCKED",dark:"DARK / frozen",ruled_out:"RULED OUT",unmapped:"UNMAPPED status"};
const SCLASS={wins:"win",active:"act",shadow:"shd",not_implemented:"ni",blocked:"blk",dark:"dark",ruled_out:"ro",unmapped:"unm"};
// Green means one thing: the cell's own pre-registered verdict at judged n is positive (builder: scripts/cell_display_state.py).
// Never derive it from the registry status alone; an absent `d` falls back to the registry status, which is never "wins".
const dstate=c=>c&&(c.d||(SCLASS[c.s]?c.s:"unmapped"));
function matrix(filter="all",q=""){
  let h=`<table><thead><tr><th class="m"></th>`;
  BANDS.forEach(b=>h+=`<th class="b">${b}</th>`);
  h+=`</tr></thead><tbody>`;
  MARKETS.forEach(([mk,label])=>{
    if(q && !(label.toLowerCase().includes(q)||mk.toLowerCase().includes(q))) return;
    h+=`<tr><th class="m">${label}</th>`;
    BANDS.forEach(b=>{
      const key=mk+"|"+b, cell=CELLS[key], st=dstate(cell);
      let cls="cellbox none", dim="";
      if(st){ cls="cellbox "+SCLASS[st];
        const keep = filter==="all" || (filter==="act"&&(st==="active"||st==="wins")) ||
                     (filter==="log"&&(st==="shadow"||st==="active"||st==="wins")) || (filter==="blk"&&st==="blocked") ||
                     (filter==="win"&&st==="wins");
        if(!keep) dim="opacity:.14";
      }
      const note = MXNOTE[key] || (cell && cell.n) || "";
      const tip = st ? encodeURIComponent(`<div class="h">${label} · ${b}</div>`+
        `<div class="r"><span>registry</span><b>${SLABEL[st]}</b></div>`+
        (note?`<div style="margin-top:6px;font-size:11.3px;color:var(--ink-2);max-width:300px;white-space:normal">${esc(note)}</div>`:"")) : "";
      h+=`<td><div class="${cls}" ${st?`data-s="${st}" data-tip="${tip}"`:""} style="${dim}">`+
         `${key==="MLB_PLAYER_PROP_HITS|T4M-PROJ"?'<span class="g">!</span>':''}</div></td>`;
    });
    h+=`</tr>`;
  });
  $('#mxHost').innerHTML=h+`</tbody></table>`;
  $$('#mxHost .cellbox[data-tip]').forEach(c=>{
    c.addEventListener('mousemove',e=>showTip(e,decodeURIComponent(c.dataset.tip)));
    c.addEventListener('mouseleave',hideTip);
  });
}

function arms(){
  $('#nvArms').textContent=ARMS.length;
  $('#armsBody').innerHTML=ARMS.map(([a,n,st,c,p,look,note])=>
    `<tr><td class="k">${esc(a)}</td><td class="num">${n}</td><td><span class="chip ${c}"><i></i>${esc(st)}</span></td>`+
    `<td class="mono" style="font-size:11.5px">${esc(p)}</td><td>${esc(look)}</td><td style="color:var(--ink-2)">${esc(note)}</td></tr>`).join('');
  $('#calBody').innerHTML=CAL.map(([d,e])=>`<tr><td class="k" style="white-space:nowrap">${esc(d)}</td><td>${esc(e)}</td></tr>`).join('');
}

function timeline(){
  $('#waveRange').textContent='29 → '+WAVES[WAVES.length-1].w; $('#nvWaves').textContent=WAVES.length;
  $('#tl').innerHTML=WAVES.slice().reverse().map(w=>
    `<div class="tlitem ${w.k}"><div class="th"><span class="tw">Wave ${w.w}</span>`+
    `<span class="chip ${w.k==='hit'?'good':w.k==='neg'?'crit':w.k==='now'?'info':'mute'}"><i></i>${
      w.k==='hit'?'moved':w.k==='neg'?'hard negative':w.k==='now'?'in flight':'closed'}</span>`+
    `<span style="font-size:12.6px;color:var(--ink);font-weight:550">${w.t}</span></div>`+
    `<div class="td">${w.d}</div></div>`).join('');
}
function desk(){
  $('#deskCount').textContent=DESK.length+' open'; $('#nvDesk').textContent=DESK.length;
  $('#deskList').innerHTML=DESK.map(d=>
    `<div class="dkrow" style="--accent:${d.a}"><div><div class="dt">${d.t}</div></div>`+
    `<div class="dd">${d.d}</div><div class="dc">${d.c}</div></div>`).join('');
}


function integrity(){
  const live=RUNTIME.filter(c=>c.status==="live"), unrev=live.filter(c=>!c.reviewed),
        noal=live.filter(c=>String(c.alarm||"").startsWith("none")||String(c.alarm||"").startsWith("UNSET"));
  $('#surfLive').textContent=live.length; $('#surfUnrev').textContent=unrev.length; $('#surfNoAlarm').textContent=noal.length;
  $('#nvInteg').textContent=live.length;
  const LR=LIVE.rows||{}, hasLive=!!LIVE.rows, isBad=(st)=>["DOWN","BEHIND","STALE","NO ALARM"].includes(st);
  if(hasLive){
    const red=LIVE.budget==="RED";
    $('#surfBudget').innerHTML=`<span style="color:var(--${red?"crit":"good"})">${esc(LIVE.budget)}</span>`;
    $('#surfBudgetN').innerHTML=(red?LIVE.reasons.map(esc).join("<br>"):"No stale, down or behind component; healthcheck and silent arms clean.")+
      `<br><span class="mono" style="font-size:11px">box probe ${esc(LIVE.as_of)} · HEAD ${esc(LIVE.head)}</span>`;
  }
  const g=GAGENT||{};
  if(g.ok){
    const bad=g.stale, good=g.running;
    $('#gaOpen').textContent=g.open_now;
    $('#gaOpenN').innerHTML=`At the agent's first tick: <b>${esc(g.open_first)}</b> (${g.delta==null?"n/a":(g.delta>0?"+":"")+g.delta}). Closed A/B/C: ${esc(g.closed.A)}/${esc(g.closed.B)}/${esc(g.closed.C)} · triaged ${esc(g.triaged)} · ${esc(g.ticks)} ticks.`;
    $('#gaState').innerHTML=`<span style="color:var(--${bad?"crit":good?"good":"warn"})">${esc(g.state_line)}</span>`;
    $('#gaStateN').textContent=`Last tick ${g.last_tick||"n/a"} (from GG_BURNDOWN.md at build time).`;
  } else { $('#gaOpen').textContent="—"; $('#gaOpenN').textContent="No gap-agent data: "+(g.error||"not read"); $('#gaState').textContent="no data"; }
  const pill={"BREADTH":"good","DEPTH":"info","EXECUTION":"warn","PROOF":"serious","PLUMBING":"mute"};
  const rowsOf=(f)=>RUNTIME.filter(c=>f==="all"||(f==="noalarm"?(c.status==="live"&&(String(c.alarm).startsWith("none")||String(c.alarm).startsWith("UNSET"))):f==="stale"?(LR[c.key]&&isBad(LR[c.key].state)):c.pillar===f));
  const draw=(f)=>{
    $('#rtBody').innerHTML=rowsOf(f).map(c=>{
      const al=String(c.alarm||""); const bad=al.startsWith("none")||al.startsWith("UNSET");
      const lv=LR[c.key]; const lbad=lv&&isBad(lv.state);
      const lcell=!hasLive?`<td style="color:var(--ink-3)">—</td>`:lv?`<td style="color:var(--${lbad?"crit":"ink-2"});white-space:nowrap">${esc(lv.state)}${lv.age_h==null?"":" · "+esc(lv.age_h)+"h"}${lv.detail?"<br>"+esc(lv.detail):""}</td>`:`<td style="color:var(--ink-3)">—</td>`;
      return `<tr${lbad?' style="background:rgba(255,80,80,.08)"':''}><td class="k">${esc(c.kind)}</td><td class="mono" style="font-size:11px;white-space:nowrap">${esc(c.schedule||"—")}</td>`+
        `<td>${esc(String(c.purpose).replace(" (auto - review)",""))}${c.status!=="live"?` <span class="chip mute"><i></i>${esc(c.status)}</span>`:""}</td>`+
        `<td><span class="chip ${pill[c.pillar]||"mute"}"><i></i>${esc(c.pillar)}</span></td>`+
        `<td style="color:${bad?"var(--crit)":"var(--ink-2)"}">${esc(al.replace(" (auto)",""))}</td>`+
        `<td>${c.reviewed?'<span class="chip good"><i></i>yes</span>':'<span class="chip warn"><i></i>no</span>'}</td>`+lcell+`</tr>`;}).join('');
  };
  draw("all");
  $$('.rtf').forEach(b=>b.addEventListener('click',()=>{$$('.rtf').forEach(o=>o.classList.remove('on')); b.classList.add('on'); draw(b.dataset.f);}));
  bars('#winTally',WINERR.tally.map(x=>[x.pattern,x.count,x.pattern==="UNVERIFIED"?"var(--crit)":"var(--warn)"]));
  $('#winCount').textContent=WINERR.rows.length;
  $('#winBody').innerHTML=WINERR.rows.slice().reverse().map(r=>
    `<tr><td class="k">${esc(r.id)}</td><td style="white-space:nowrap">${esc(r.date)}</td><td>${esc(r.what)}</td>`+
    `<td><span class="chip warn"><i></i>${esc(r.pattern)}</span></td><td style="color:var(--ink-2)">${esc(r.rule)}</td></tr>`).join('');
}
function govCounts(){
  $$('.govOpen').forEach(e=>e.textContent=GOV.open); $$('.govLive').forEach(e=>e.textContent=GOV.live);
  $$('.govRetired').forEach(e=>e.textContent=GOV.retired);
  const st={}; Object.values(CELLS).forEach(c=>{const k=dstate(c); st[k]=(st[k]||0)+1;});
  const n=Object.keys(CELLS).length, logging=(st.shadow||0)+(st.active||0)+(st.wins||0);
  $$('.cellN').forEach(e=>e.textContent=n); $('#mxLogging').textContent=logging;
  $('#mxBreak').textContent=`${st.wins||0} WINS, ${st.active||0} ACTIVE, ${st.shadow||0} SHADOW`;
  $('#mxOther').textContent=`${st.blocked||0} are BLOCKED, ${st.dark||0} DARK ${st.ruled_out?`, ${st.ruled_out} RULED OUT`:""}${st.unmapped?`, ${st.unmapped} UNMAPPED`:""} and ${st.not_implemented||0} defined but not built`;
}

/* ---- WIRE ---- */

/* ---------- PICKS SHEET (W97.3) ---------- */
function picksSheet(){
  const D=PICKS, host=$('#pkHost');
  if(!D||!D.ok){ host.innerHTML=`<div class="card pk-err"><b>No picks sheet to show.</b><div class="cap">${esc((D&&D.error)||'missing')}. The nightly builder writes it after the arms' decision passes; nothing is drawn rather than a blank list.</div></div>`; $('#pkHead').textContent='no sheet'; $('#nvPicks').textContent='!'; return; }
  const sheet=(S,withRes)=>{
    if(!S) return '<div class="card pk-err"><b>No sheet for this day.</b></div>';
    if(!S.games.length) return `<div class="card pk-err"><b>The sheet for ${esc(S.date)} has no picks.</b><div class="cap">${esc((S.notes||[]).join(' · ')||'no arm found a positive edge in the window')}</div></div>`;
    return S.games.map(g=>{
      const rows=g.picks.map(p=>{
        const o=p.demo_order, od=o?(o.placed?`demo order $${esc(o.stake_usd)}`:`no order (${esc(o.reason)})`):'no order logged';
        const r=withRes&&p.result?` · <b>${esc(p.result.outcome)}</b> ${p.result.pnl_per_contract>=0?'+':''}${esc(p.result.pnl_per_contract)}/contract`:'';
        return `<li><b>${esc(p.pick)}</b> <span class="cap">[${esc(p.arm)}]</span><br>bot ${Math.round(p.bot_prob_for_pick*100)}% · Kalshi ${Math.round(p.kalshi_price_yes*100)}¢ (yes) · edge ${(p.edge_after_fee*100).toFixed(1)}¢ after fees · ${od}${r}<br><span class="cap">why: ${esc(p.reasons.join('; '))}</span></li>`;
      }).join('');
      return `<div class="card"><div class="bl-h"><span class="bl-title">${esc(g.game)}</span>${g.arms_disagree?'<span class="bl-id">ARMS DISAGREE</span>':''}</div><ul>${rows}</ul></div>`;
    }).join('');
  };
  $('#pkHead').textContent=D.today.n_picks+' picks · '+D.today.games.length+' games'; $('#nvPicks').textContent=D.today.n_picks;
  host.innerHTML=`<h3 class="bl-grp">Tonight<small>${esc(D.today.date)}</small></h3>${sheet(D.today,false)}<h3 class="bl-grp">Yesterday, with results<small>${D.yesterday?esc(D.yesterday.date):''}</small></h3>${sheet(D.yesterday,true)}`;
}

/* ---------- ROLLING BACKLOG ---------- */
function backlog(){
  const D=BACKLOG, host=$('#blHost');
  if(!D||!D.ok){ host.innerHTML=`<div class="card bl-err"><b>The backlog's source file did not validate.</b><div class="cap">${esc((D&&D.error)||'missing')}. Nothing is drawn rather than a wrong list.</div></div>`; $('#blHead').textContent='source invalid'; $('#nvBacklog').textContent='!'; return; }
  const n=D.tickets.length, open=D.tickets.filter(t=>t.status!=='DONE').length;
  $('#blHead').textContent=open+' open · '+n+' tickets'; $('#nvBacklog').textContent=open;
  let h=`<div class="bl-top"><div class="bl-asof">as of ${esc(D.as_of)}</div><ol class="bl-rank">${D.ranking.map(r=>`<li>${esc(r)}</li>`).join('')}</ol></div>`;
  for(const [g,ts] of D.groups){
    if(!ts.length) continue;
    h+=`<h3 class="bl-grp">${esc(g)}<small>${esc((D.statuses&&D.statuses[g])||'')} · ${ts.length}</small></h3><div class="bl-list">`;
    for(const t of ts){
      const tags=['lane','rank','wave'].filter(k=>t[k]).map(k=>`<span>${k} ${esc(t[k])}</span>`).join('');
      const row=(k,l)=>t[k]?`<dt>${l}</dt><dd>${esc(t[k])}</dd>`:'';
      h+=`<div class="card bl-t${g==='DONE'?' done':''}"><div class="bl-h"><span class="bl-id">${esc(t.id)}</span><span class="bl-title">${esc(t.title)}</span></div>`+
         `<div class="bl-tags"><span>#${esc(t.order)}</span>${tags}</div><dl>${row('measure','measure')}${row('why','why')}${row('source','source')}</dl></div>`;
    }
    h+='</div>';
  }
  host.innerHTML=h;
}

/* ---------- AGGREGATION WEB (Muse) — expandable graph ---------- */
function museWeb(){
  const D=MUSEWEB, host=$('#mwHost');
  if(!D||!D.ok){ host.innerHTML=`<div class="cap mw-err">The web's source file did not validate (${esc((D&&D.error)||'missing')}). Nothing is drawn rather than a wrong picture.</div>`; $('#mwHead').textContent='source invalid'; return; }
  const SVGNS='http://www.w3.org/2000/svg', ST={built:'b',pending:'p',future:'f'}, SL={b:'built',p:'pending',f:'future'};
  const R={hub:24,sport:17,ws:10,step:6.5,ticket:5.5,unit:8,group:7,item:4};
  const LEN={sport:180,ws:118,step:50,ticket:74,unit:62,group:56,item:58};
  const CH={hub:1600,sport:1400,ws:1000,step:160,ticket:220,unit:340,group:280,item:260};
  const PAD={hub:18,sport:22,ws:40,step:12,ticket:12,unit:18,group:16,item:12};
  // NFL has 19 position groups; a unit layer (offense skill, OL, DL, LB, secondary) keeps the graph navigable — positions stay separate
  const UNITS={nfl:[['SKILL','Offense skill',['QB','RB','WR','TE']],['OL','Offensive line',['LT','LG','C','RG','RT']],['DL','Defensive line',['EDGE','DT3','NT','DE5']],['LB','Linebackers',['MIKE','WILL','SAM']],['DB','Secondary',['CB','FS','SS']]]};
  const N=new Map(), add=(n)=>{ n.children=n.children||[]; n.parents=n.parents||[]; n.x=n.y=n.vx=n.vy=0; n.seen=false; N.set(n.id,n); return n; };
  const link=(p,c)=>{ p.children.push(c.id); c.parents.push(p.id); };
  const cnt=v=>({b:v.filter(z=>z==='b').length, p:v.filter(z=>z==='p').length, f:v.filter(z=>z==='f').length, n:v.length});
  // ---- build the tree (plus shared ticket nodes)
  const hub=add({id:'hub',kind:'hub',label:'Muse',sub:'aggregation'});
  const allSteps=[];
  D.sports.forEach(sp=>{
    const s=add({id:'s:'+sp,kind:'sport',label:sp}); link(hub,s);
    D.spokes.filter(x=>x.sport===sp).forEach((x,wi)=>{
      const st=x.states.map(z=>ST[z]), w=add({id:`w:${sp}:${wi}`,kind:'ws',label:x.name,sport:sp,steps:st,spoke:x,
        state: st.includes('b')?'b':(st.includes('p')?'p':'f')}); link(s,w);
      st.forEach((z,i)=>{ const n=add({id:`${w.id}:r${i}`,kind:'step',label:D.rings[i].label,state:z,ring:i,ws:w.id,note:(x.notes||[])[i]||''});
        link(w,n); allSteps.push(n);
        if(i===2 && x.taxonomy && D.taxonomy[x.taxonomy]){ const T=D.taxonomy[x.taxonomy]; n.tax=T;
          const units=new Map(); (UNITS[x.taxonomy]||[]).forEach(([uid,ul,gs])=>{ const un=add({id:`${n.id}:u:${uid}`,kind:'unit',label:ul,state:z,sport:sp,gs}); link(n,un); gs.forEach(gid=>units.set(gid,un)); });
          T.groups.forEach(g=>{ const gn=add({id:`${n.id}:g:${g.id}`,kind:'group',label:g.label,state:z,g,tax:T,sport:sp}); link(units.get(g.id)||n,gn);
            g.items.forEach(it=>link(gn,add({id:`${gn.id}:${it.id}`,kind:'item',label:it.id,name:it.name,state:z,it,group:g.label,sport:sp}))); }); }
      });
      (x.tickets||'').split('·').map(t=>t.trim()).filter(t=>/^R-\d{3}$/.test(t)).forEach(t=>{
        const tn=N.get('t:'+t)||add({id:'t:'+t,kind:'ticket',label:t,info:D.tickets[t]||null}); link(w,tn); });
    });
  });
  N.forEach(n=>{ if(n.kind==='ticket'){ const ws=n.parents.map(p=>N.get(p)); n.state=ws.some(w=>w.steps.includes('p'))?'p':'f'; }});
  N.forEach(n=>{ n.r=R[n.kind]; n.ch=CH[n.kind]; n.pad=PAD[n.kind]; });
  const T=cnt(allSteps.map(n=>n.state));
  // ---- state
  const open=new Set(['hub']); let sel='hub', hov=null;
  const vis=()=>{ const v=new Set(), walk=id=>{ if(v.has(id))return; v.add(id); if(open.has(id)) N.get(id).children.forEach(walk); }; walk('hub'); return v; };
  let V=vis(), L=[];
  const seed=()=>{ // deterministic first layout: sports on diagonals, workstreams fanned outward
    D.sports.forEach((sp,k)=>{ const a=(-45+90*k)*Math.PI/180, s=N.get('s:'+sp); s.x=Math.cos(a)*150; s.y=Math.sin(a)*150; s.seen=true;
      s.children.forEach((c,i,arr)=>{ const w=N.get(c), b=a+(i-(arr.length-1)/2)*0.42; w.x=s.x+Math.cos(b)*84; w.y=s.y+Math.sin(b)*84; w.seen=true; }); });
    hub.seen=true; };
  // ---- svg scaffold
  host.innerHTML=`<svg class="mw-g" role="img" aria-label="Aggregation graph: Muse's work by sport, workstream, step and taxonomy"><g class="vp"><g class="lk"></g><g class="nds"></g></g></svg>`;
  const svg=host.querySelector('svg'), vp=svg.querySelector('.vp'), gL=svg.querySelector('.lk'), gN=svg.querySelector('.nds');
  let view={x:0,y:0,k:1};
  const setView=()=>{ vp.setAttribute('transform',`translate(${view.x},${view.y}) scale(${view.k})`); svg.style.setProperty('--k',view.k); svg.classList.toggle('far',view.k<0.8); svg.classList.toggle('near',view.k>=1.35); };
  const size=()=>{ const r=svg.getBoundingClientRect(); return [r.width||800,r.height||600]; };
  const el=(tag,attrs,parent)=>{ const e=document.createElementNS(SVGNS,tag); for(const k in attrs)e.setAttribute(k,attrs[k]); if(parent)parent.appendChild(e); return e; };
  const arc=(r,a0,a1)=>{ const p=a=>[r*Math.cos(a),r*Math.sin(a)], [x0,y0]=p(a0), [x1,y1]=p(a1); return `M${x0.toFixed(2)},${y0.toFixed(2)}A${r},${r} 0 ${a1-a0>Math.PI?1:0} 1 ${x1.toFixed(2)},${y1.toFixed(2)}`; };
  const DOM=new Map();
  const hidden=n=>n.children.filter(c=>!V.has(c)).length;
  function makeNode(n){
    const g=el('g',{class:`nd k-${n.kind} s-${n.state||'n'}`}); g.dataset.id=n.id;
    if(n.kind==='hub'){ el('circle',{class:'core',r:n.r},g); }
    else if(n.kind==='sport'){ el('circle',{class:'core',r:n.r},g);
      const c=cnt(n.children.flatMap(w=>N.get(w).steps)), tot=c.n||1; let a=-Math.PI/2; const gap=0.05;
      [['b',c.b],['p',c.p],['f',c.f]].forEach(([k,v])=>{ if(!v)return; const da=v/tot*2*Math.PI; el('path',{class:'seg s-'+k,d:arc(n.r+4.5,a+gap/2,a+da-gap/2)},g); a+=da; }); }
    else if(n.kind==='ws'){ el('circle',{class:'core',r:n.r},g);
      const k=n.steps.length, gap=0.16; n.steps.forEach((z,i)=>{ const a0=-Math.PI/2+i*2*Math.PI/k+gap/2, a1=a0+2*Math.PI/k-gap; el('path',{class:'seg s-'+z,d:arc(n.r+3.8,a0,a1)},g); }); }
    else if(n.kind==='ticket'){ el('rect',{class:'core',x:-n.r,y:-n.r,width:2*n.r,height:2*n.r,rx:1.8,transform:'rotate(45)'},g); }
    else { el('circle',{class:'core',r:n.r},g); }
    if(n.kind==='hub'){ el('text',{class:'in hk',y:-3},g).textContent='MUSE'; el('text',{class:'in hv',y:9},g).textContent=`${T.b}/${T.n}`; }
    else if(n.kind==='sport'){ el('text',{class:'in sk',y:4},g).textContent=n.label; }
    const lab=el('text',{class:'lab',y:n.r+(n.kind==='ws'||n.kind==='sport'?17:12.5),'text-anchor':'middle'},g);
    if(n.kind==='hub') lab.textContent='steps built';
    else if(n.kind!=='sport'){ lab.textContent=n.kind==='item'?`${n.label} · ${n.name}`:n.label; }
    const bd=el('g',{class:'bd',transform:`translate(${(n.r+2)*0.78},${-(n.r+2)*0.78})`},g); el('circle',{r:6.2},bd); el('text',{y:2.6},bd);
    g.addEventListener('pointerenter',()=>{ hov=n.id; paintHL(); });
    g.addEventListener('pointerleave',()=>{ hov=null; paintHL(); });
    g.addEventListener('pointerdown',e=>startDrag(e,n));
    return g;
  }
  function sync(){
    V=vis();
    V.forEach(id=>{ const n=N.get(id); if(!n.seen){ const p=N.get(n.parents.find(q=>V.has(q)&&open.has(q))||n.parents[0]); const gp=p&&N.get(p.parents.find(q=>V.has(q))||''); const sib=p?p.children.indexOf(id):0, m=p?p.children.length:1;
        const base=p?(gp?Math.atan2(p.y-gp.y,p.x-gp.x):Math.atan2(p.y,p.x)):0, spread=Math.min(Math.PI*1.6,0.5*m), a=base+(m>1?(sib/(m-1)-0.5)*spread:0);
        n.x=(p?p.x:0)+Math.cos(a)*(LEN[n.kind]||40)*0.6; n.y=(p?p.y:0)+Math.sin(a)*(LEN[n.kind]||40)*0.6; n.vx=n.vy=0; n.seen=true; } });
    L=[]; V.forEach(id=>{ const n=N.get(id); if(open.has(id)) n.children.forEach(c=>{ if(V.has(c)) L.push([n,N.get(c)]); }); });
    DOM.forEach((g,id)=>{ if(!V.has(id)){ g.remove(); DOM.delete(id); } });
    V.forEach(id=>{ if(!DOM.has(id)){ const g=makeNode(N.get(id)); DOM.set(id,g); } });
    // paint order: deep first so parents sit on top
    const depth={item:0,group:1,unit:2,ticket:2,step:2,ws:3,sport:4,hub:5};
    [...V].sort((a,b)=>depth[N.get(a).kind]-depth[N.get(b).kind]).forEach(id=>gN.appendChild(DOM.get(id)));
    gL.innerHTML=''; L.forEach(([a,b])=>{ const l=el('line',{class:`ln k-${b.kind}`},gL); l._a=a; l._b=b; });
    DOM.forEach((g,id)=>{ const n=N.get(id), h=hidden(n); g.classList.toggle('has',h>0); g.classList.toggle('open',open.has(id)&&n.children.length>0);
      g.querySelector('.bd text').textContent=h>99?'99+':h; g.classList.toggle('sel',id===sel); });
    paintHL(); heat(0.7);
  }
  function paintHL(){
    const focus=hov||null, nb=new Set();
    if(focus){ nb.add(focus); const n=N.get(focus); n.children.forEach(c=>V.has(c)&&nb.add(c)); n.parents.forEach(p=>V.has(p)&&nb.add(p)); }
    svg.classList.toggle('hovering',!!focus);
    DOM.forEach((g,id)=>g.classList.toggle('hl',nb.has(id)));
    gL.querySelectorAll('line').forEach(l=>l.classList.toggle('hl',!!focus&&(l._a.id===focus||l._b.id===focus)));
    // labels of items show near the selection
    const sn=N.get(sel); DOM.forEach((g,id)=>{ const n=N.get(id); g.classList.toggle('ctx', n.kind==='item' && (n.parents.includes(sel) || id===sel || (sn&&sn.parents.includes(id)))); });
  }
  // ---- physics (small, dependency-free force layout)
  let alpha=0, raf=0;
  const heat=a=>{ alpha=Math.max(alpha,a); if(!raf) raf=requestAnimationFrame(step); };
  function tick(){
    const ns=[...V].map(id=>N.get(id));
    for(let i=0;i<ns.length;i++){ const a=ns[i];
      for(let j=i+1;j<ns.length;j++){ const b=ns[j]; let dx=b.x-a.x, dy=b.y-a.y, d2=dx*dx+dy*dy;
        if(d2<1){ dx=(Math.random()-.5); dy=(Math.random()-.5); d2=1; }
        if(d2>250000) continue; const f=(a.ch+b.ch)*0.5*alpha/d2, fx=dx*f, fy=dy*f;
        a.vx-=fx/a.ch*90; a.vy-=fy/a.ch*90; b.vx+=fx/b.ch*90; b.vy+=fy/b.ch*90;
        const md=a.r+b.r+a.pad+b.pad; if(d2<md*md){ const d=Math.sqrt(d2), o=(md-d)/d*0.5; a.x-=dx*o; a.y-=dy*o; b.x+=dx*o; b.y+=dy*o; } } }
    L.forEach(([p,c])=>{ const want=LEN[c.kind]*(c.kind==='ticket'?1:1), dx=c.x-p.x, dy=c.y-p.y, d=Math.sqrt(dx*dx+dy*dy)||1, f=(d-want)/d*alpha*0.5;
      const wp=p.kind==='hub'?0:0.35, wc=1-wp; p.vx+=dx*f*wp; p.vy+=dy*f*wp; c.vx-=dx*f*wc; c.vy-=dy*f*wc; });
    ns.forEach(n=>{ if(n.kind==='hub'||n.fx!=null){ n.x=n.fx??0; n.y=n.fy??0; n.vx=n.vy=0; return; }
      n.vx-=n.x*0.0025*alpha; n.vy-=n.y*0.0025*alpha; n.vx*=0.58; n.vy*=0.58; n.x+=n.vx; n.y+=n.vy; });
    alpha*=0.975;
  }
  function step(){ raf=0; tick(); draw(); if(alpha>0.004) raf=requestAnimationFrame(step); else alpha=0; }
  const settle=(k,a)=>{ alpha=Math.max(alpha,a); for(let i=0;i<k;i++) tick(); };
  // labels sit on the side facing away from the parent, so fans of siblings don't stack their labels
  const OFF={ws:5,sport:6};
  function place(g,n){ if(n.kind==='hub'||n.kind==='sport')return; const p=N.get(n.parents.find(q=>V.has(q)&&open.has(q))||''); if(!p)return;
    const dx=n.x-p.x, dy=n.y-p.y, d=Math.hypot(dx,dy)||1, c=dx/d, sn=dy/d, o=n.r+(OFF[n.kind]||0)+5;
    const side=c>0.42?'r':c<-0.42?'l':sn>=0?'b':'t'; if(g._side===side)return; g._side=side; const t=g.querySelector('.lab');
    if(side==='r'){ t.setAttribute('x',o); t.setAttribute('y',3.5); t.setAttribute('text-anchor','start'); }
    else if(side==='l'){ t.setAttribute('x',-o); t.setAttribute('y',3.5); t.setAttribute('text-anchor','end'); }
    else if(side==='b'){ t.setAttribute('x',0); t.setAttribute('y',o+8); t.setAttribute('text-anchor','middle'); }
    else { t.setAttribute('x',0); t.setAttribute('y',-o-1); t.setAttribute('text-anchor','middle'); } }
  function draw(){
    DOM.forEach((g,id)=>{ const n=N.get(id); g.setAttribute('transform',`translate(${n.x.toFixed(1)},${n.y.toFixed(1)})`); place(g,n); });
    gL.querySelectorAll('line').forEach(l=>{ l.setAttribute('x1',l._a.x.toFixed(1)); l.setAttribute('y1',l._a.y.toFixed(1)); l.setAttribute('x2',l._b.x.toFixed(1)); l.setAttribute('y2',l._b.y.toFixed(1)); });
  }
  // ---- view: pan, zoom, drag, fit
  const toWorld=(cx,cy)=>{ const r=svg.getBoundingClientRect(); return [(cx-r.left-view.x)/view.k,(cy-r.top-view.y)/view.k]; };
  let tween=0;
  const animateTo=(x,y,k)=>{ cancelAnimationFrame(tween); const s={...view}, t0=performance.now();
    const f=t=>{ const u=Math.min(1,(t-t0)/380), e=1-Math.pow(1-u,3); view={x:s.x+(x-s.x)*e,y:s.y+(y-s.y)*e,k:s.k+(k-s.k)*e}; setView(); if(u<1) tween=requestAnimationFrame(f); }; tween=requestAnimationFrame(f); };
  const fit=(ids,maxK=1.6)=>{ const [w,h]=size(), ns=[...(ids||V)].map(id=>N.get(id)); if(!ns.length)return;
    let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity; ns.forEach(n=>{ x0=Math.min(x0,n.x-n.r-60); x1=Math.max(x1,n.x+n.r+60); y0=Math.min(y0,n.y-n.r-30); y1=Math.max(y1,n.y+n.r+34); });
    const pr=panelW(), k=Math.min(maxK,(w-pr-24)/(x1-x0),(h-24)/(y1-y0)); animateTo((w-pr)/2-(x0+x1)/2*k, h/2-(y0+y1)/2*k, Math.max(0.3,k)); };
  const panelW=()=>{ const p=$('#mwPanel'); return p && getComputedStyle(p).position==='absolute' ? p.offsetWidth+16 : 0; };
  const centerOn=(n,k)=>{ const [w,h]=size(), kk=k||Math.max(view.k,1.1), pr=panelW(); animateTo((w-pr)/2-n.x*kk, h/2-n.y*kk, kk); };
  let drag=null;
  function startDrag(e,n){ e.stopPropagation(); svg.setPointerCapture(e.pointerId); drag={n,id:e.pointerId,x:e.clientX,y:e.clientY,moved:false}; }
  const ptrs=new Map(); let pan=null, pinch=null;
  svg.addEventListener('pointerdown',e=>{ if(drag)return; ptrs.set(e.pointerId,[e.clientX,e.clientY]); svg.setPointerCapture(e.pointerId);
    if(ptrs.size===2){ const [a,b]=[...ptrs.values()]; pinch={d:Math.hypot(a[0]-b[0],a[1]-b[1]),k:view.k,mx:(a[0]+b[0])/2,my:(a[1]+b[1])/2}; pan=null; }
    else pan={x:e.clientX,y:e.clientY,vx:view.x,vy:view.y,moved:false}; });
  svg.addEventListener('pointermove',e=>{
    if(drag&&e.pointerId===drag.id){ if(Math.hypot(e.clientX-drag.x,e.clientY-drag.y)>4) drag.moved=true;
      if(drag.moved&&drag.n.kind!=='hub'){ const [wx,wy]=toWorld(e.clientX,e.clientY); drag.n.fx=wx; drag.n.fy=wy; heat(0.25); } return; }
    if(ptrs.has(e.pointerId)) ptrs.set(e.pointerId,[e.clientX,e.clientY]);
    if(pinch&&ptrs.size===2){ const [a,b]=[...ptrs.values()], d=Math.hypot(a[0]-b[0],a[1]-b[1]); zoomAt(pinch.mx,pinch.my,pinch.k*d/pinch.d,true); return; }
    if(pan){ const dx=e.clientX-pan.x, dy=e.clientY-pan.y; if(Math.abs(dx)+Math.abs(dy)>3) pan.moved=true; view.x=pan.vx+dx; view.y=pan.vy+dy; setView(); } });
  const up=e=>{
    if(drag&&e.pointerId===drag.id){ const n=drag.n; if(!drag.moved) clickNode(n); else { n.fx=n.fy=null; heat(0.2); } drag=null; return; }
    ptrs.delete(e.pointerId); if(ptrs.size<2) pinch=null; if(pan&&!pan.moved&&e.type==='pointerup') { /* background click: keep selection */ } pan=null; };
  svg.addEventListener('pointerup',up); svg.addEventListener('pointercancel',up);
  function zoomAt(cx,cy,k,abs){ const r=svg.getBoundingClientRect(), nk=Math.max(0.3,Math.min(4,abs?k:view.k*k)), px=cx-r.left, py=cy-r.top;
    view.x=px-(px-view.x)*nk/view.k; view.y=py-(py-view.y)*nk/view.k; view.k=nk; setView(); }
  svg.addEventListener('wheel',e=>{ e.preventDefault(); zoomAt(e.clientX,e.clientY,Math.exp(-e.deltaY*0.0016)); },{passive:false});
  // ---- interaction
  const pathTo=id=>{ const out=[]; let n=N.get(id); while(n){ out.unshift(n); const p=n.parents.find(q=>V.has(q))||n.parents[0]; n=p?N.get(p):null; } return out; };
  const hood=n=>[n.id,...n.parents.filter(p=>V.has(p)),...n.children.filter(c=>V.has(c))];
  function clickNode(n){
    let opened=false;
    if(n.children.length){ if(open.has(n.id) && sel===n.id){ collapse(n.id); } else if(!open.has(n.id)){ open.add(n.id); opened=true; } }
    sel=n.id; sync(); panel();
    if(opened){ settle(70,0.7); draw(); fit(hood(n),1.5); } }
  const collapse=id=>{ const walk=x=>{ open.delete(x); N.get(x).children.forEach(c=>{ if(N.get(c).parents.length<=1||!N.get(c).parents.some(p=>p!==x&&open.has(p))) walk(c); }); }; walk(id); };
  function focus(id,{expand=true,zoom}={}){ const ps=pathTo(id); ps.slice(0,-1).forEach(n=>open.add(n.id)); if(expand&&N.get(id).children.length) open.add(id);
    sel=id; sync(); panel(); settle(70,0.7); draw(); const n=N.get(id); if(open.has(id)&&n.children.length) fit(hood(n),zoom||1.5); else centerOn(n,zoom); }
  // ---- detail panel
  const pill=z=>`<span class="mw-st s-${z}">${SL[z]||z}</span>`;
  const dots=st=>`<span class="mw-dots">${st.map((z,i)=>`<i class="s-${z}" title="${esc(D.rings[i].label)}: ${SL[z]}"></i>`).join('')}</span>`;
  const go=(id,txt,cls='')=>`<button class="mw-go ${cls}" data-go="${esc(id)}">${txt}</button>`;
  function panel(){
    const n=N.get(sel), P=$('#mwPanel'); if(!n){ P.innerHTML=''; return; }
    const crumbs=pathTo(sel).map((x,i,a)=>i<a.length-1?go(x.id,esc(x.kind==='item'?x.label:x.label)):`<b>${esc(x.kind==='item'?x.label:x.label)}</b>`).join('<span class="sep">›</span>');
    let h=`<div class="mw-crumb">${crumbs}</div>`;
    const kindName={hub:'Overview',sport:'Sport',ws:'Workstream',step:'Step',ticket:'Muse ticket',unit:'Position unit',group:'Position group',item:'Taxonomy entry'}[n.kind];
    h+=`<div class="mw-kind">${kindName}</div>`;
    if(n.kind==='hub'){
      h+=`<h4>Muse's aggregation work</h4><div class="mw-ptiles"><div><b class="c-b">${T.b}</b><span>built</span></div><div><b class="c-p">${T.p}</b><span>pending</span></div><div><b class="c-f">${T.f}</b><span>future</span></div></div>`;
      h+=`<div class="mw-sec">By sport</div>`+D.sports.map(sp=>{ const c=cnt(N.get('s:'+sp).children.flatMap(w=>N.get(w).steps)), t=c.n||1;
        return `<button class="mw-row" data-go="s:${esc(sp)}"><span class="nm">${esc(sp)}</span><span class="mw-bar"><i class="s-b" style="width:${c.b/t*100}%"></i><i class="s-p" style="width:${c.p/t*100}%"></i></span><span class="ct">${c.b} · ${c.p} · ${c.f}</span></button>`; }).join('');
      h+=`<p class="mw-hint">Click a node to open it; click it again to close it. Drag nodes, drag the background to pan, scroll or pinch to zoom.</p>`;
    } else if(n.kind==='sport'){
      const ws=n.children.map(c=>N.get(c)), c=cnt(ws.flatMap(w=>w.steps));
      h+=`<h4>${esc(n.label)}</h4><div class="mw-ptiles"><div><b class="c-b">${c.b}</b><span>built</span></div><div><b class="c-p">${c.p}</b><span>pending</span></div><div><b class="c-f">${c.f}</b><span>future</span></div></div>`;
      h+=`<div class="mw-sec">Workstreams · ${ws.length}</div>`+ws.map(w=>`<button class="mw-row" data-go="${esc(w.id)}"><span class="nm">${esc(w.label)}</span>${dots(w.steps)}</button>`).join('');
    } else if(n.kind==='ws'){
      const x=n.spoke, tk=n.children.filter(c=>c.startsWith('t:')).map(c=>N.get(c));
      h+=`<h4>${esc(n.label)}</h4><div class="mw-meta">${pill(n.state)} ${dots(n.steps)}</div>`;
      h+=`<div class="mw-sec">Steps, scouted → applied</div>`+n.children.filter(c=>N.get(c).kind==='step').map(c=>{ const s=N.get(c);
        return `<button class="mw-row step" data-go="${esc(s.id)}"><span class="nm">${pill(s.state)} ${esc(s.label)}</span>${s.note?`<span class="nt">${esc(s.note)}</span>`:''}</button>`; }).join('');
      if(tk.length) h+=`<div class="mw-sec">Tickets</div>`+tk.map(t=>`<button class="mw-row" data-go="${esc(t.id)}"><span class="nm mono">${esc(t.label)}</span><span class="nt">${esc((t.info&&t.info.title)||'')}</span></button>`).join('');
    } else if(n.kind==='step'){
      const w=N.get(n.ws), ring=D.rings[n.ring];
      h+=`<h4>${esc(ring.label)} <span class="mw-of">· ${esc(w.label)}</span></h4><div class="mw-meta">${pill(n.state)}</div><p class="mw-desc">${esc(ring.desc)}</p>`;
      if(n.note) h+=`<div class="mw-sec">Where it stands</div><p>${esc(n.note)}</p>`;
      if(n.tax){ const items=n.tax.groups.reduce((s,g)=>s+g.items.length,0);
        h+=`<div class="mw-sec">PAM taxonomy · ${esc(n.tax.status)}</div><p class="mw-desc">${n.tax.groups.length} groups · ${items} entries · <span class="mono">${esc(n.tax.file)}</span></p>`+
          n.tax.groups.map(g=>go(`${n.id}:g:${g.id}`,`${esc(g.label)} <span class="ct">${g.items.length}</span>`,'chip')).join(''); }
    } else if(n.kind==='ticket'){
      h+=`<h4><span class="mono">${esc(n.label)}</span></h4><div class="mw-meta">${pill(n.state)}</div>`;
      h+=n.info?`<p><b>${esc(n.info.title)}</b></p><p class="mw-desc">${esc(n.info.text)}</p>`:`<p class="mw-desc">Not found in TO_MUSE.md.</p>`;
      h+=`<div class="mw-sec">Feeds</div>`+n.parents.map(p=>{ const w=N.get(p); return `<button class="mw-row" data-go="${esc(w.id)}"><span class="nm">${esc(w.sport)} · ${esc(w.label)}</span>${dots(w.steps)}</button>`; }).join('');
    } else if(n.kind==='unit'){
      const gs=n.children.map(c=>N.get(c)); h+=`<h4>${esc(n.label)}</h4><div class="mw-meta">${pill(n.state)} <span class="mw-of">${gs.length} positions · ${gs.reduce((a,g)=>a+g.g.items.length,0)} archetypes</span></div>`;
      h+=gs.map(g=>`<button class="mw-row" data-go="${esc(g.id)}"><span class="nm">${esc(g.label)}</span><span class="ct">${g.g.items.length}</span><span class="nt">${g.g.items.map(i=>esc(i.name)).join(' · ')}</span></button>`).join('');
    } else if(n.kind==='group'){
      h+=`<h4>${esc(n.label)}</h4><div class="mw-meta">${pill(n.state)} <span class="mw-of">${n.g.items.length} ${n.g.kind==='modifier'?'modifiers':'archetypes'} · ${esc(n.tax.status)}</span></div>`;
      h+=n.children.map(c=>{ const it=N.get(c); return `<button class="mw-row" data-go="${esc(it.id)}"><span class="nm"><span class="mono">${esc(it.label)}</span> ${esc(it.name)}</span>${it.it.notes?`<span class="nt">${esc(it.it.notes)}</span>`:''}</button>`; }).join('');
    } else if(n.kind==='item'){
      const it=n.it; h+=`<h4>${esc(n.name)}</h4><div class="mw-meta"><span class="mono mw-of">${esc(n.label)} · ${esc(n.group)}</span></div>`;
      [['What it is',it.notes],['Signals',it.signals],['Draft threshold',it.threshold]].forEach(([k,v])=>{ if(v) h+=`<div class="mw-sec">${k}</div><p>${esc(v)}</p>`; });
      h+=`<p class="mw-hint">Draft, awaiting your approval. Thresholds are a-priori and get calibrated when the mass tier is built.</p>`;
    }
    if(n.children.length) h+=`<div class="mw-act"><button class="btn sm" data-tog="1">${open.has(n.id)?'Close':'Open'} · ${n.children.length}</button><button class="btn sm" data-fitsel="1">Frame</button></div>`;
    P.innerHTML=h;
    P.querySelectorAll('[data-go]').forEach(b=>b.addEventListener('click',()=>focus(b.dataset.go,{expand:true})));
    const tg=P.querySelector('[data-tog]'); if(tg) tg.addEventListener('click',()=>{ if(open.has(n.id)) collapse(n.id); else open.add(n.id); sync(); panel(); });
    const fs=P.querySelector('[data-fitsel]'); if(fs) fs.addEventListener('click',()=>{ const ids=[n.id,...n.children.filter(c=>V.has(c))]; fit(ids,2.2); });
  }
  // ---- toolbar
  const index=[...N.values()].filter(n=>n.kind!=='hub'&&n.kind!=='step').map(n=>({id:n.id, t:(n.kind==='item'?`${n.label} ${n.name}`:n.kind==='ws'?`${n.sport} · ${n.label}`:(n.kind==='group'||n.kind==='unit')?`${n.sport} PAM · ${n.label}`:n.label)}));
  $('#mwFilters').innerHTML=`<div class="mw-seg">${['All',...D.sports].map((f,i)=>`<button class="btn sm mwf${i?'':' on'}" data-f="${esc(f)}">${esc(f)}</button>`).join('')}</div>`+
    `<label class="mw-search"><input id="mwQ" list="mwQL" placeholder="Find a workstream, ticket, archetype…" autocomplete="off"><datalist id="mwQL">${index.map(x=>`<option value="${esc(x.t)}"></option>`).join('')}</datalist></label>`+
    `<span class="spacer"></span><button class="btn sm" id="mwOpenAll">Open all</button><button class="btn sm" id="mwReset">Reset</button><button class="btn sm" id="mwFit">Fit</button>`;
  const setF=f=>{ $$('#mwFilters .mwf').forEach(x=>x.classList.toggle('on',x.dataset.f===f));
    open.clear(); open.add('hub'); (f==='All'?D.sports:[f]).forEach(sp=>open.add('s:'+sp));
    sel=f==='All'?'hub':'s:'+f; sync(); panel(); settle(90,0.6); draw();
    fit(f==='All'?null:['s:'+f,...N.get('s:'+f).children],1.3); };
  $$('#mwFilters .mwf').forEach(b=>b.addEventListener('click',()=>setF(b.dataset.f)));
  $('#mwQ').addEventListener('change',e=>{ const q=e.target.value.trim().toLowerCase(); const hit=index.find(x=>x.t.toLowerCase()===q)||index.find(x=>x.t.toLowerCase().includes(q)); if(hit){ focus(hit.id,{expand:false,zoom:1.5}); e.target.blur(); } });
  $('#mwFit').addEventListener('click',()=>fit());
  $('#mwReset').addEventListener('click',()=>{ open.clear(); open.add('hub'); D.sports.forEach(sp=>open.add('s:'+sp)); sel='hub'; N.forEach(n=>{ n.seen=false; n.fx=n.fy=null; }); seed(); sync(); panel(); settle(220,0.9); draw(); fit(); });
  $('#mwOpenAll').addEventListener('click',()=>{ N.forEach(n=>{ if(n.children.length) open.add(n.id); }); sync(); panel(); settle(160,0.9); draw(); fit(); });
  // ---- tiles + open-now list
  const tile=(k,v,acc,n)=>`<div class="tile" style="--accent:${acc}"><div class="k">${k}</div><div class="v">${v}</div><div class="n">${n}</div></div>`;
  const openT=[...N.values()].filter(n=>n.kind==='ticket'&&n.state==='p').length;
  $('#mwTiles').innerHTML=tile('Built',T.b,'var(--s1)','steps delivered')+tile('Pending',T.p,'var(--warn)','steps with a ticket or block open')+tile('Future',T.f,'var(--axis)','planned, no ticket yet')+tile('Tickets open',openT,'var(--ink-3)','Muse tickets feeding pending steps');
  const pend=[...N.values()].filter(n=>n.kind==='ws'&&n.steps.includes('p'));
  $('#mwOpen').innerHTML=pend.map(w=>`<div class="mw-orow"><div class="hd"><span class="sp">${esc(w.sport)}</span><button class="w mw-go" data-go="${esc(w.id)}">${esc(w.label)}</button><span class="tg">${esc(w.spoke.tickets)}</span></div>`+
    w.children.filter(c=>N.get(c).kind==='step'&&N.get(c).state==='p').map(c=>{ const s=N.get(c); return `<div class="ln"><button class="st mw-go" data-go="${esc(s.id)}">${esc(s.label)}</button><span class="d">${esc(s.note)}</span></div>`; }).join('')+`</div>`).join('');
  $$('#mwOpen [data-go]').forEach(b=>b.addEventListener('click',()=>{ $('#museweb').scrollIntoView({behavior:'smooth',block:'start'}); focus(b.dataset.go,{expand:false,zoom:1.4}); }));
  $('#mwHead').textContent=`${pend.length} workstreams with open steps · ${T.b} of ${T.n} steps built`;
  $('#nvMuse').textContent=T.p;
  $('#mwSrc').innerHTML=`Source <span class="mono">QUAL_ARCHIVE/MUSE_WEB.json</span> (kept by the strategic window at every wave close), <span class="mono">TO_MUSE.md</span> and the PAM taxonomies · as of <span class="mono">${esc(D.as_of||'?')}</span> · archive <span class="mono">${esc(D.archive_commit||'?')}</span>`;
  // ---- go
  D.sports.forEach(sp=>open.add('s:'+sp)); seed(); sync(); panel(); setView();
  cancelAnimationFrame(raf); raf=0; settle(220,0.9); alpha=0; draw();
  const ro=new ResizeObserver(()=>fit()); ro.observe(host); fit();
}

distance(); forest(); bars('#funnel',FUNNEL); matrix(); arms(); timeline(); desk(); integrity(); govCounts(); museWeb(); backlog(); picksSheet();
bars('#sevBars',SEV); bars('#asymBars',ASYM);
$('#tblBtn').addEventListener('click',()=>{
  const t=$('#forestTable'); t.classList.toggle('hidden');
  $('#tblBtn').textContent = t.classList.contains('hidden') ? '▤ Table view' : '▤ Hide table';
});
let mxF="all", mxQ="";
$$('.mxf').forEach(b=>b.addEventListener('click',()=>{
  $$('.mxf').forEach(o=>o.classList.remove('on')); b.classList.add('on');
  mxF=b.dataset.f; matrix(mxF,mxQ);
}));
$('#mxSearch').addEventListener('input',e=>{mxQ=e.target.value.trim().toLowerCase(); matrix(mxF,mxQ);});
$('#themeBtn').addEventListener('click',()=>{
  const cur=document.documentElement.getAttribute('data-theme')||'dark';
  const next=cur==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',next);
  try{localStorage.setItem('pmb-theme',next)}catch(e){}
});
try{const s=localStorage.getItem('pmb-theme'); if(s)document.documentElement.setAttribute('data-theme',s);}catch(e){}
const secs=$$('section[id]'), navs=$$('.rail a.nv');
const io=new IntersectionObserver(es=>{
  es.forEach(en=>{ if(en.isIntersecting){
    navs.forEach(a=>a.classList.toggle('on', a.getAttribute('href')==='#'+en.target.id));
  }});
},{rootMargin:'-80px 0px -70% 0px', threshold:0});
secs.forEach(s=>io.observe(s));
