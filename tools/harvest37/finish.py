"""Round 36 (quench runs the harvest pass): keep the driver alive until the search deadline, then stop it.
Slimmed from harvest34/finish.py: no take close, no report and no commit here (the quench lane reports)."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import W,END,state,write_json


def stop_driver():
    p=W/'driver.pid'
    if not p.exists():return
    pid=int(p.read_text())
    check=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=5)
    if '/harvest37/driver.py' in check.stdout:
        try:os.killpg(pid,signal.SIGTERM)
        except ProcessLookupError:pass
        state(f'STOP owned driver pid={pid} before search deadline06:45Z')


def ensure_driver(now):
    if now>=END-300:return
    pidpath=W/'driver.pid'
    pid=int(pidpath.read_text()) if pidpath.exists() else 0
    check=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=5) if pid else None
    if check and '/harvest37/driver.py' in check.stdout:return
    restarts=W/'driver-restarts.json'
    history=json.loads(restarts.read_text()) if restarts.exists() else []
    history=[value for value in history if now-value<3600]
    if history and now-history[-1]<60:return
    if len(history)>=3:return
    history.append(now);write_json(restarts,history)
    command=[sys.executable,'-I',str(Path(__file__).with_name('driver.py'))]
    with (W/'driver.log').open('a') as log:
        child=subprocess.Popen(['nice','-n','5']+command,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
    pidpath.write_text(str(child.pid)+'\n')
    state(f'REVIVE absent owned driver as pid={child.pid}; command={command}, log={W}/driver.log, deadline06:45Z')


def main():
    while time.time()<END-120:
        try:ensure_driver(time.time())
        except Exception as exc:state('HEALTH check deferred: '+type(exc).__name__)
        time.sleep(10)
    stop_driver()
    state('FINAL harvest37 supervisor exits after the driver stop')

if __name__=='__main__':main()
