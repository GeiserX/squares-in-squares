"""Collect completed quench receipts without waiting for broad donor intake."""
import datetime,json,os,subprocess,time
from pathlib import Path
import coordinator as C
W=Path(C.WORK);END=datetime.datetime(2026,11,14,2,53,tzinfo=datetime.timezone.utc).timestamp()
state=W/'publisher-state.json'
C.S['published']=set(json.load(open(state))) if state.exists() else set()
while time.time()<END and not (W/'STOP_PUBLISHER').exists():
    try:
        for host,key in C.HOSTS:
            dest=W/'boxcopy'/key/'final';dest.mkdir(parents=True,exist_ok=True)
            r=subprocess.run(['rsync','-az',host+':scratch/squares-stair-c/final/',str(dest)+'/'],capture_output=True,text=True,timeout=50)
            if r.returncode:print(C.stamp(),'receipt copy failed',host,r.stderr,flush=True)
        C.publish()
        tmp=Path(str(state)+'.tmp');tmp.write_text(json.dumps(sorted(C.S['published'])));tmp.replace(state)
    except Exception:
        import traceback
        traceback.print_exc()
    time.sleep(25)
print(C.stamp(),'PUBLISHER STOPPED',flush=True)
