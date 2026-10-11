/* ============================================================ DATA (edited by the strategic window at each wave close) */
const DIST = [
  ["Breadth","B1","Cells logging / registered","37 / 104","the whole board","0 — NBA points not wired (65.1)"],
  ["Breadth","B2","Families with a logging cell","12 / 18","18 / 18, props + parlays registered","0"],
  ["Breadth","B3","Bands with a logging cell","4 of 5 (no T5)","5 of 5, T4 sub-bands","0"],
  ["Breadth","B4","Props · parlay families logging","1 · 0","the board's props and parlays","0 — the 1 ends with the World Series"],
  ["Depth","D1","Factor classes per pre-game model","NFL team only; nobody uses matchup, weather, qualitative","every class at every arm","0 — NFL personnel goes live in 65.3"],
  ["Depth","D2","Largest pre-game feature set","18 (MLB hits, 0 qualitative)","coverage of classes, not a count","0"],
  ["Depth","D3","Pre-registered challengers ready","1 (NFL QB-shrunk)","≥ 1 per arm before its first look","+1"],
  ["Execution","E1","Demo orders filled","T4 166 / 4,237 · T1 85 / 485","fills ≈ intended orders","0 — fix accepted 10-10"],
  ["Execution","E2","P&L per filled bet","T4 −$0.26 · T1 −$1.50","positive, net of fees","0"],
  ["Execution","E3","Win rate, fills vs non-fills","T4 24.1% vs 48.7% · T1 28.9% vs 52.1%","fills at least as good","0 — forward test ON in 65.2"],
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
  "NBA_PLAYER_POINTS|T4":"Legacy NBA book, frozen. T1–T3 cells arrive with 65.1 (EXP-039).",
};

const ARMS = [
  ["NFL game markets",12,"Logging","good","EXP-037","~2026-11-02","15 of 60 games per cell; first look most likely \"keep accruing\""],
  ["NFL QB-shrunk challenger",2,"Ships in 65.3","warn","accepted 10-10","with EXP-037 vs the market","Moneyline; first live NFL model that knows who plays"],
  ["MLB postseason game markets",12,"Logging","good","EXP-037 MLB","2027 regular season","Postseason rows logged, not scored"],
  ["MLB player hits T1–T3",3,"Logging","good","—","—","Stops with the World Series"],
  ["MLB player hits T4M-PROJ",1,"Active · demo stakes","good","ADR-0050","—","Stakes stop for every game after the World Series"],
  ["NHL game markets",9,"Logging","good","EXP-036","preliminary all 2026-27","Judged sample not reachable this season (GG-514)"],
  ["NBA game markets",12,"Preseason","warn","EXP-038","150 games per cell","Regular season from 10-20; cells flip ~10-21"],
  ["NBA player points T1–T3",3,"Pre-registered","warn","EXP-039","after opening night","Model, runner and cron in 65.1 — must log from 10-20"],
];
const CAL = [
  ["10-11 → 10-12","ADR-0072 forward test switched on (65.2), after a 1-contract demo canary verifies the cancel call"],
  ["Mon 10-12","Weekly T4 ledger rebuild — first live test of the overwrite guard"],
  ["Thu 10-15","First NFL slate the QB challenger can log (65.3)"],
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
  {w:"65", k:"now", t:"NBA points live · forward test ON · NFL challenger logging.",
   d:"Aimed at Breadth (B4 1 → 2, B1 37 → 40), Execution (first treatment fills) and Depth (NFL personnel in a live model)."},
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

const SEV = [["CRITICAL",2,"var(--crit)"],["HIGH",17,"var(--serious)"],["MEDIUM",45,"var(--warn)"],
             ["LOW",45,"var(--s1)"],["UNSPECIFIED",21,"var(--ink-3)"]];
const ASYM = [["Registered, ever",378,"var(--s2)"],["Retired to archive",223,"var(--s3)"],["Live",155,"var(--s1)"],["Live and OPEN",130,"var(--warn)"]];
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

const SLABEL={active:"ACTIVE",shadow:"SHADOW — evaluates and logs",not_implemented:"Defined, not implemented",blocked:"BLOCKED",dark:"DARK / frozen"};
const SCLASS={active:"act",shadow:"shd",not_implemented:"ni",blocked:"blk",dark:"dark"};
function matrix(filter="all",q=""){
  let h=`<table><thead><tr><th class="m"></th>`;
  BANDS.forEach(b=>h+=`<th class="b">${b}</th>`);
  h+=`</tr></thead><tbody>`;
  MARKETS.forEach(([mk,label])=>{
    if(q && !(label.toLowerCase().includes(q)||mk.toLowerCase().includes(q))) return;
    h+=`<tr><th class="m">${label}</th>`;
    BANDS.forEach(b=>{
      const key=mk+"|"+b, cell=CELLS[key], st=cell&&cell.s;
      let cls="cellbox none", dim="";
      if(st){ cls="cellbox "+SCLASS[st];
        const keep = filter==="all" || (filter==="act"&&st==="active") ||
                     (filter==="log"&&(st==="shadow"||st==="active")) || (filter==="blk"&&st==="blocked");
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

/* ---- WIRE ---- */
distance(); forest(); bars('#funnel',FUNNEL); matrix(); arms(); timeline(); desk();
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
