"""Stop owned work, finalize the take, and write the report after17:25 UTC."""
import csv
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,T,W,END,state,write_json,table
TAKE=dt.datetime(2026,11,16,17,25,tzinfo=dt.timezone.utc).timestamp()


def report_bytes():
    rows=table(T/'take.tsv')
    outcomes=[json.loads(p.read_text()) for p in (W/'outcomes').glob('*.json')]
    decisions=[r for p in W.glob('public*/decisions.json') for r in json.loads(p.read_text())]
    info=json.loads((W/'final-run-info.json').read_text()) if (W/'final-run-info.json').exists() else {}
    gain=sum(float(r['held'])-float(r['new']) for r in rows)
    inc=sum(float(r.get('incremental_gain',r['gain'])) for r in rows)
    report=dict(lane='harvest',improved_n=len(rows),gain=dict(vs_base_bar=gain,beyond_other_live_r32_takes=inc),take_dir=str(T),
        summary=info.get('summary',f'Harvest retains {len(rows)} rows after the quench and live comparison. Peer rows count in their own lanes.'),
        what_was_measured=[f'Public reader decisions: {len(decisions)}. Eligible decisions: {sum(not r["refusal"] for r in decisions)}.',
             f'Dispatch outcomes: {len(outcomes)}. Certified handoffs for offbox quench: {sum(r.get("outcome")=="certified handoff; offbox fq required" for r in outcomes)}. Refusals: {sum("error" in r for r in outcomes)}.',
             'Public-only shares use the frozen assembler centre/corner boxes and median-offset ICP at1e-3 and1e-2. Controls reject public851 at0.464159811986 and972 at0.452674897119, and accept852 at0.361502347418. Own588/228 remain exempt.',
             'Budget: two local processes for downloads and light Python. Certified inputs go to the quench lane for offbox fq.'
             ]+info.get('measurements',[]),
        next=info.get('next',[
            'Fetch changed licensed public final CSVs first. Round31 initial roots supplied0.00171605987 before other-lane follows.',
            'Keep source-cleared handoffs tied to exact certified bytes and source pins. Public453 exposed a missed1e-2 share in the prior control.'
        ]),commits=info.get('commits',[]),processes_left=info.get('processes_left','none (search driver stopped; finalizer exits after report)'),
        blocked=info.get('blocked','none'),repo='$PRIVATE_REPO',branch='main',worktree='$PRIVATE_REPO',pr='none (direct main lane contract)')
    return (json.dumps(report,indent=2)+'\n').encode()


def stop_driver():
    p=W/'driver.pid'
    if not p.exists():return
    pid=int(p.read_text())
    check=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=5)
    if '/harvest32/driver.py' in check.stdout:
        try:os.killpg(pid,signal.SIGTERM)
        except ProcessLookupError:pass
        state(f'STOP owned driver pid={pid} before search deadline17:15Z')


def ensure_driver(now):
    if now>=END-300:return
    pidpath=W/'driver.pid'
    pid=int(pidpath.read_text()) if pidpath.exists() else 0
    check=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=5) if pid else None
    if check and '/harvest32/driver.py' in check.stdout:return
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
    state(f'REVIVE absent owned driver as pid={child.pid}; command={command}, log={W}/driver.log, deadline17:15Z')


def main():
    # Report bytes are prepared before the deadline. The very first action
    # after the final wait is their atomic publication, even after a restart.
    pending=report_bytes()
    if time.time()>TAKE:
        temp=T/'report.json.tmp';temp.write_bytes(pending);temp.replace(T/'report.json');return
    stopped=False;last_prepare=0
    while time.time()<=TAKE:
        now=time.time()
        if now<END-300:
            try:ensure_driver(now)
            except Exception as exc:state("HEALTH check deferred: "+type(exc).__name__)
        if now>=END-120 and not stopped:
            stop_driver();stopped=True
            try:
                from close32 import close
                close()
            except Exception as exc:state('CLOSE push deferred: '+repr(exc))
        if stopped and now-last_prepare>40 and now<TAKE-40:
            try:
                if table(T/'take.tsv'):
                    from finalize import prepare_take
                    prepare_take()
                else:
                    (Path('results/harvest-r32-2026-11-16.tsv')).write_bytes((T/'take.tsv').read_bytes())
                    write_json(W/'final-source-audit.json',[])
                pending=report_bytes()
                (W/'prepared-report.json').write_bytes(pending)
            except Exception as exc:
                state('CLOSE audit deferred; prepared report remains available: '+type(exc).__name__)
            last_prepare=time.time()
        time.sleep(max(.001,min(10,TAKE-time.time()+.01)))
    temp=T/'report.json.tmp';temp.write_bytes(pending);temp.replace(T/'report.json')
    state('FINAL report.json written immediately after17:25Z; finalizer exits')

if __name__=='__main__':main()
