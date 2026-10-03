"""T-621: drop the tunnel mid-session and report what the page shows. Usage: python ... <port> <ssh-pid>"""
import os, signal, sys, time
from playwright.sync_api import sync_playwright
port, pid = sys.argv[1], int(sys.argv[2])
with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None); pg = b.new_page(viewport={"width": 1600, "height": 1000})
    pg.goto(f"http://localhost:{port}/", wait_until="domcontentloaded")
    pg.wait_for_function("document.getElementById('sha').textContent.trim()!=='—'", timeout=60000)
    pg.wait_for_timeout(1500)
    snap = lambda: pg.evaluate("""()=>({banner:(document.querySelector('#banner,.banner')||{}).innerText||null,
      kpi:[...document.querySelectorAll('.kpi,.k')].slice(0,6).map(e=>e.innerText.replace(/\\n/g,' ')),
      head:document.body.innerText.slice(0,400).replace(/\\n/g,' | ')})""")
    a = snap(); pg.wait_for_timeout(5000); a2 = snap()
    print("LIVE t0     :", a["head"]); print("LIVE t0+5s  :", a2["head"])
    os.kill(pid, signal.SIGKILL); t = time.time()
    for _ in range(3):
        pg.wait_for_timeout(30000)
        s = snap(); print(f"+{int(time.time()-t)}s after kill:", s["banner"], "||", s["head"])
    pg.screenshot(path=(sys.argv[3] if len(sys.argv)>3 else "exp_output/w48_3_screens")+"/index.tunnel_dropped.png", full_page=False)
    b.close()
