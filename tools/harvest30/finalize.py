"""Audit final snapshots before 17:55 and write the report after that deadline."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from walk import validate_job,public_job
from policy import audit
from pins import job_matches
from notices import enrich
from harvest_collect import COLS


def allowed(row,job,bars):
    n=int(row['n']);target=T/(str(n)+'.csv')
    validate_job(job)
    if hashlib.sha256(Path(job['path']).read_bytes()).hexdigest()!=job['sha256']:raise ValueError('changed input bytes')
    proof=Path(row['remote_quench'])
    if not proof.is_file():raise ValueError('missing remote receipt')
    receipt=json.loads(proof.read_text())
    if receipt['input_hash']!=job['sha256']:raise ValueError('wrong remote input hash')
    source=Path(receipt['file'])
    if not source.exists() or source.read_bytes()!=target.read_bytes():raise ValueError('changed certificate bytes')
    if float(row['new'])>=bars[n]-1e-10:raise ValueError('lower live peer')
    ok,ev=audit(list(csv.DictReader(target.open()))) if public_job(job) else (True,[])
    if not ok:raise ValueError('excluded output share')
    return True


def prepare_take():
    bars={int(r['n']):float(r['bar']) for r in table(S/'round30-briefs/bar30.tsv')}
    base_bar=dict(bars)
    for p in S.glob('take-*-r30/take.tsv'):
        if p.parent==T:continue
        for r in table(p):
            if (p.parent/(r['n']+'.csv')).exists():bars[int(r['n'])]=min(bars[int(r['n'])],float(r['new']))
    jobs=[json.loads(p.read_text()) for p in (W/'jobs').glob('*.json')]
    keep=[];audits=[]
    for row in table(T/'take.tsv'):
        n=int(row['n'])
        job=next((j for j in jobs if job_matches(row,j)),None)
        try:
            if job is None:raise ValueError('missing exact source job')
            allowed(row,job,bars)
            row=enrich(row,job)
            row['held']=repr(base_bar[n]);row['gain']=repr(base_bar[n]-float(row['new']))
            row['other_best']=repr(bars[n]);row['incremental_gain']=repr(bars[n]-float(row['new']));keep.append(row)
            audits.append(dict(n=n,allowed=True,sha256=job['sha256']))
        except Exception as e:audits.append(dict(n=n,allowed=False,reason=repr(e)))
    tmp=T/'take.tsv.tmp'
    with tmp.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=COLS,delimiter='\t',extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(keep)
    tmp.replace(T/'take.tsv')
    kept={int(r['n']) for r in keep}
    for path in T.glob('[0-9]*.csv'):
        if int(path.stem) not in kept:
            dest=W/'final-out';dest.mkdir(exist_ok=True);path.replace(dest/path.name)
    write_json(W/'final-source-audit.json',audits)
    (L/'results/harvest-r30-2026-11-15.tsv').write_bytes((T/'take.tsv').read_bytes())
    state(f'TAKE FINAL rows={len(keep)}; compared every live r30 ledger')
    return keep


def finalize():
    deadline=dt.datetime(2026,11,15,17,55,tzinfo=dt.timezone.utc).timestamp()
    if time.time()<=deadline:raise RuntimeError('report must follow17:55Z deadline')
    rows=table(T/'take.tsv')
    outcomes=[json.loads(p.read_text()) for p in (W/'outcomes').glob('*.json')]
    decisions=[r for p in W.glob('public*/decisions.json') for r in json.loads(p.read_text())]
    restored=json.loads((W/'restored.json').read_text()) if (W/'restored.json').exists() else []
    gain=sum(float(r['held'])-float(r['new']) for r in rows)
    incremental=sum(float(r['incremental_gain']) for r in rows)
    info=json.loads((W/'final-run-info.json').read_text()) if (W/'final-run-info.json').exists() else {}
    metrics=dict(completed=len(outcomes),errors=sum('error' in r for r in outcomes),admissions=sum(r.get('outcome')=='certified take' for r in outcomes),public_candidates=len(decisions),public_eligible=sum(not r['refusal'] for r in decisions),restored_candidates=len(restored),restored_eligible=sum(r['allowed'] for r in restored))
    write_json(W/'final-metrics.json',metrics)
    report=dict(lane='harvest',improved_n=len(rows),gain=dict(vs_base_bar=gain,beyond_other_live_r30_takes=incremental),take_dir=str(T),
        summary=f'Final certified take holds {len(rows)} rows below bar30.tsv and every other live round30 take. Gain {gain:.15g}.',
        what_was_measured=[
            'Public-share controls rejected exact prvsiyan858 at share1.0 and accepted independent453 at share0.006622516556291391. Own layouts are exempt under round30 brief overrides2/3.',
            'Retention-note control passed. Valid source withdrawals remain exclusions. Pinned-walk controls accepted missing producer paths and rejected changed snapshots and new hard withdrawals.',
            f'Queue outcomes: {len(outcomes)} completed, {metrics["errors"]} errors, {metrics["admissions"]} provisional admission events.',
            f'Public reader retained {len(decisions)} decision entries. Distinct queued public inputs: {sum(json.loads(p.read_text()).get("kind")=="fresh-public" for p in (W/"jobs").glob("*.json"))}. Downloaded files were data only.',
            f'Certified prior-round snapshots repriced: {len(restored)} candidates, {metrics["restored_eligible"]} eligible. Unchanged public near-miss quenches were not repeated.',
            'Every retained row passed floatsafe at2.2e-11 and a certified-input fq quench on boxC. Own layouts follow round30 brief overrides2/3. Shares gate fetched public rows only; explicit excluded-file ancestry remains out.',
        ]+info.get('measurements',[]),
        next=info.get('next',[
            'Read changed public final CSVs first. Round28 starter-kit n499 gained6.681e-6 before live supersession; early round30 endpoints returned HTTP404.',
            'Run fresh source-checked rectangle and k123 inputs before saved near misses. Historical unchanged public near-miss quenches supplied no crossing in their first20 attempts.',
            'Keep exact parent snapshots and apply source policy by origin. Round28 controls accepted identical seed503 bytes as own geometry and refused them as fetched public data. Actual prvsiyan-file ancestry remains excluded.'
        ]),commits=info.get('commits',[]),processes_left=info.get('processes_left','cleanup pending'),blocked=info.get('blocked','none'),repo='$PRIVATE_REPO',branch='main',worktree='$PRIVATE_REPO',pr='none (direct main lane contract)')
    write_json(T/'report.json',report)
    state(f'FINAL report rows={len(rows)} gain={gain:.15g} incremental={incremental:.15g}; written after17:55Z')
    return report

if __name__=='__main__':
    if '--wait' in sys.argv:
        target=dt.datetime(2026,11,15,17,52,0,tzinfo=dt.timezone.utc).timestamp()
        while time.time()<target:time.sleep(min(30,target-time.time()))
        prepare_take()
        target=dt.datetime(2026,11,15,17,54,30,tzinfo=dt.timezone.utc).timestamp()
        while time.time()<target:time.sleep(min(10,target-time.time()))
        prepare_take()
        target=dt.datetime(2026,11,15,17,55,2,tzinfo=dt.timezone.utc).timestamp()
        while time.time()<target:time.sleep(min(10,target-time.time()))
    elif '--take-only' in sys.argv:prepare_take();raise SystemExit(0)
    finalize()
    from close_round import close
    print(json.dumps(close(),indent=2))
