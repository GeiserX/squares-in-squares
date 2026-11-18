"""Stop owned work, finalize the take, and write the report after00:25 UTC."""
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
TAKE=dt.datetime(2026,11,16,0,25,tzinfo=dt.timezone.utc).timestamp()


def report_bytes():
    rows=table(T/'take.tsv')
    outcomes=[json.loads(p.read_text()) for p in (W/'outcomes').glob('*.json')]
    decisions=[r for p in W.glob('public*/decisions.json') for r in json.loads(p.read_text())]
    info=json.loads((W/'final-run-info.json').read_text()) if (W/'final-run-info.json').exists() else {}
    gain=sum(float(r['held'])-float(r['new']) for r in rows)
    inc=sum(float(r.get('incremental_gain',r['gain'])) for r in rows)
    report=dict(lane='harvest',improved_n=len(rows),gain=dict(vs_base_bar=gain,beyond_other_live_r31_takes=inc),take_dir=str(T),
        summary=f'Final take contains {len(rows)} certified rows below bar31 and the other live takes. Unquenched handoffs are not counted.',
        what_was_measured=[f'Public reader decisions: {len(decisions)}; eligible: {sum(not r["refusal"] for r in decisions)}.',
             f'Dispatch outcomes: {len(outcomes)}; certified offbox-quench handoffs: {sum(r.get("outcome")=="certified handoff; offbox fq required" for r in outcomes)}; refusals: {sum("error" in r for r in outcomes)}.',
             'Public-only shares use the frozen assembler centre/corner boxes and median-offset ICP at1e-3 and1e-2. Controls reject public851 at0.464159811986 and972 at0.452674897119, and accept852 at0.361502347418. Own588/228 remain exempt.',
             'The assigned budget is two local download/light-Python processes. No remote search seat is assumed. Offbox fq work is handed through the round31 log.'
             ]+info.get('measurements',[]),
        next=info.get('next',[
            'Fetch changed public outputs first. Round30 changed228 gave6.899e-5 and round29 public848 gave4.929e-4.',
            'Keep source-cleared handoffs tied to exact certified bytes and source pins. Public453 exposed a missed1e-2 share in the prior control.'
        ]),commits=info.get('commits',[]),processes_left=info.get('processes_left','none (search driver stopped; finalizer exits after report)'),
        blocked=info.get('blocked','none'),repo='$PRIVATE_REPO',branch='main',worktree='$PRIVATE_REPO',pr='none (direct main lane contract)')
    return (json.dumps(report,indent=2)+'\n').encode()


def stop_driver():
    p=W/'driver.pid'
    if not p.exists():return
    pid=int(p.read_text())
    check=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True)
    if '/harvest31/driver.py' in check.stdout:
        os.killpg(pid,signal.SIGTERM);state(f'STOP owned driver pid={pid} at search deadline00:15Z')


def main():
    # Report bytes are prepared before the deadline. The very first action
    # after the final wait is their atomic publication, even after a restart.
    pending=report_bytes()
    if time.time()>TAKE:
        temp=T/'report.json.tmp';temp.write_bytes(pending);temp.replace(T/'report.json');return
    stopped=False;last_prepare=0
    while time.time()<=TAKE:
        now=time.time()
        if now>=END and not stopped:
            stop_driver();stopped=True
        if now>END and now-last_prepare>40 and now<TAKE-40:
            try:
                if table(T/'take.tsv'):
                    from finalize import prepare_take
                    prepare_take()
                else:
                    (Path('results/harvest-r31-2026-11-16.tsv')).write_bytes((T/'take.tsv').read_bytes())
                    write_json(W/'final-source-audit.json',[])
                pending=report_bytes()
                (W/'prepared-report.json').write_bytes(pending)
            except Exception as exc:
                state('CLOSE audit deferred; prepared report remains available: '+type(exc).__name__)
            last_prepare=time.time()
        time.sleep(max(.001,min(10,TAKE-time.time()+.01)))
    temp=T/'report.json.tmp';temp.write_bytes(pending);temp.replace(T/'report.json')
    state('FINAL report.json written immediately after00:25Z; finalizer exits')

if __name__=='__main__':main()
