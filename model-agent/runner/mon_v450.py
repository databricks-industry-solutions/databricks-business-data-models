#!/usr/bin/env python3
"""v4.5.0 shipping monitor (fe-gcp). Append a status block every POLL_S to /tmp/v450_mon.txt.
Read-only. Exits when the run TERMINATES. Automotive (fe-aws) is monitored separately if auth restored."""
import json, subprocess, time
from datetime import datetime, timezone

PROF, RID, CAT, IND = "fe-gcp", "521695476500351", "vibe_shipping_ports_v1", "shipping_ports"
OUT, POLL_S = "/tmp/v450_mon.txt", 180

def now(): return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def sh(cmd, t=120):
    try: return subprocess.run(cmd, capture_output=True, text=True, timeout=t).stdout
    except Exception as e: return f"__ERR__ {e}"

def state():
    d = json.loads(sh(["databricks","jobs","get-run",RID,"--profile",PROF,"-o","json"]) or "{}")
    s = d.get("state",{})
    tasks=[(t.get("task_key"),t.get("state",{}).get("life_cycle_state"),t.get("state",{}).get("result_state")) for t in d.get("tasks",[])]
    return s.get("life_cycle_state"), s.get("result_state"), tasks

def info_tail():
    base=f"dbfs:/Volumes/{CAT}/_metamodel/vol_root/logs/{IND}"
    vers=sh(["databricks","fs","ls",base,"--profile",PROF],60); best=None
    for ln in vers.splitlines():
        tok=ln.split()
        if tok and tok[-1].rstrip("/").startswith(("v2","mvm","ecm")): best=tok[-1].rstrip("/")
    if not best: return "(no v2 log dir yet)"
    d2=sh(["databricks","fs","ls",f"{base}/{best}","--profile",PROF],60); info=None
    for ln in d2.splitlines():
        tok=ln.split()
        if tok and "info" in tok[-1]: info=tok[-1]
    if not info: return f"({best}: no info yet)"
    loc=f"/tmp/v450_ship.log"
    sh(["databricks","fs","cp",f"{base}/{best}/{info}",loc,"--overwrite","--profile",PROF],120)
    try:
        L=open(loc,errors="ignore").read().splitlines()
        fired=[l for l in L if "vov-named-create-targets FIRED" in l or "verifier-product-create-coverage" in l or "P0-create" in l]
        return f"[{best}/{info} lines={len(L)}] TAIL:: "+" || ".join(L[-5:])+((" || FIRED:: "+" | ".join(fired[-3:])) if fired else "")
    except Exception: return f"({best}/{info} cp-fail)"

def main():
    while True:
        lc,res,tasks=state()
        tstr=" ".join(f"{k}:{(l or '?')[:4]}/{(r or '-')[:4]}" for k,l,r in tasks)
        blk=[f"===== PULSE {now()} =====",f"[shipping/{PROF}] lc={lc} result={res} | {tstr}"]
        if lc!="TERMINATED": blk.append("  "+info_tail()[:500])
        open(OUT,"a").write("\n".join(blk)+"\n")
        if lc=="TERMINATED":
            open(OUT,"a").write(f"===== TERMINATED {now()} =====\n"); return
        time.sleep(POLL_S)

if __name__=="__main__": main()
