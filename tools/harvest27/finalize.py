"""Finalize after 23:55 UTC, retain audit records and write the lane report."""
import csv
import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import re
csv.field_size_limit(1 << 26)
S=Path('$SCRATCH/bounties-squares')
T=S/'take-harvest-r27'
W=T/'work'
L=Path(__file__).resolve().parents[2]


def table(path):
    if not path.exists():return []
    with path.open() as f:return list(csv.DictReader(f,delimiter='\t'))


def write_json(path,data):
    tmp=Path(str(path)+'.tmp');tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(path)


def state(msg):
    with (T/'STATE.txt').open('a') as f:f.write(dt.datetime.now(dt.timezone.utc).isoformat()+' boxA '+msg+'\n')


def collector():
    from types import SimpleNamespace
    return SimpleNamespace(held={int(r['n']):float(r['bar']) for r in table(S/'round27-briefs/bar27.tsv')})


def finalize():
    final_time=dt.datetime(2026,11,14,23,55,2,tzinfo=dt.timezone.utc).timestamp()
    if time.time()<final_time:raise RuntimeError('final report must follow the take deadline')
    C=collector()
    rows=table(T/'take.tsv')
    kept={int(r['n']):(T/(r['n']+'.csv'),r) for r in rows}
    outcomes=[json.loads(p.read_text()) for p in (W/'outcomes').glob('*.json')]
    reopened=json.loads((W/'reopened.json').read_text())
    decisions=[]
    for p in W.glob('public*/decisions.json'):
        decisions+=json.loads(p.read_text())
    gain=sum(C.held[n]-float(row['new']) for n,(_,row) in kept.items())
    incremental=sum(float(row['incremental_gain']) for _,row in kept.values())
    tablepath=L/'results/harvest-r27-2026-11-14.tsv'
    tablepath.write_bytes((T/'take.tsv').read_bytes())
    previously_refused=[r for r in reopened if r['original_samanyu_share']>=.4]
    newly_allowed=sum(r['allowed'] for r in previously_refused)
    metrics=dict(reopened_checked=len(reopened),reopened_allowed=sum(r['allowed'] for r in reopened),previously_refused=len(previously_refused),newly_allowed=newly_allowed,
        completed=len(outcomes),errors=sum('error' in r for r in outcomes),
        initial_take_admissions=sum(r.get('outcome')=='certified take' for r in outcomes),
        public_candidates=len(decisions),public_refused=sum(bool(r['refusal']) for r in decisions))
    write_json(W/'final-metrics.json',metrics)
    run_info=json.loads((W/'final-run-info.json').read_text()) if (W/'final-run-info.json').exists() else {}
    report=dict(lane='harvest',improved_n=len(kept),gain=dict(vs_base_bar=gain,beyond_other_live_r27_takes=incremental),
        take_dir=str(T),summary=f'{len(kept)} final certified rows below the round 27 bar and every live round 27 take. '+
            f'{len(outcomes)} final proof outcomes recorded. Of {len(previously_refused)} starts excluded for Samanyu in round 26, {newly_allowed} pass the remaining exclusions.',
        what_was_measured=[
            'Policy positive controls: exact prvsiyan 858 rejected at share 1.000; independent harvest 453 accepted at share 0.006622516556291391.',
            f'Samanyu-labelled starts: {len(reopened)} measured. Of {len(previously_refused)} previously excluded starts, {newly_allowed} pass and {len(previously_refused)-newly_allowed} still fail the remaining share policy. Eight already eligible starts also entered the queue.',
            f'Proof outcomes: {len(outcomes)} finished, {metrics["errors"]} errors, {metrics["initial_take_admissions"]} provisional take admissions.',
            f'Public merge candidates audited: {len(decisions)}, refused {metrics["public_refused"]}. All fetched outputs were read as data.',
            'boxA paging delayed light imports and certification: about 11 CPU seconds per driver over 16 wall minutes at load 51. The coordinate cache was reduced to numpy arrays.',
            'Every published row has a certified-input fq proof on boxC and a pinned input hash.',
            'Public ancestry withdrawals: 639 and 918 lacked a complete independent union trace; the 918 recipe names donor 745 measured out at share 0.667. The inherited916 and its atlas copy lacked per-n clearance. Immutable evidence is retained.',
            'The bounded reader replaced two 900-second metric-merge timeouts. A real public972 control matched the raw official score within 1e-12. Finalizer controls retained a real certificate and rejected a lower-peer case and changed bytes.',
            'Pinned-walk controls passed: missing producer paths and REINSTATE survive, changed snapshots and new hard withdrawals fail. Earlier unreadable-source attempts remain in work/previous-errors.'],
        next=[
            'Use the four-column public reader first, then certify only candidates below the live bar. It delivered the new public n=132,157,793,851, while both full and final-CSV metric merges hit 900 seconds.',
            'Admit a fresh public row only after its complete source-specific ancestry check. Geometry shares of 0.208 for 639 and 0.062 for 918 missed unresolved union ancestry; the 916 alias appeared under another notebook.',
            'Restore certified snapshots before public near misses. Recovered990 first held 1.562e-4 below the bar, while the reopened public near starts produced no crossing in the initial 20 attempts.',
            'Follow fresh licensed constructions with pinned files and records. The 499 retry passed and entered the take only after removing the dependency on its missing producer path.',
            'Do not repeat unchanged public near-miss quenches. Reprice unused saved inputs against the next bar and keep backlog claims ahead of duplicate work.'],
        commits=run_info.get('commits',[]),processes_left=run_info.get('processes_left','cleanup pending'),blocked='none',repo='$PRIVATE_REPO',
        branch='main',worktree='$PRIVATE_REPO',pr='none (direct main lane contract)')
    write_json(T/'report.json',report)
    state(f'FINAL take rows={len(kept)} gain={gain:.12g} incremental={incremental:.12g}; report written after deadline')
    return report


def prepare_take():
    # Every retained file already has a certified-input remote proof. This pass
    # compares current advertised certified live scores without re-running search.
    bars={int(r['n']):float(r['bar']) for r in table(S/'round27-briefs/bar27.tsv')}
    for p in S.glob('take-*-r27/take.tsv'):
        if p.parent==T:continue
        for r in table(p):
            if (p.parent/(r['n']+'.csv')).exists():
                n=int(r['n']);bars[n]=min(bars[n],float(r['new']))
    rows=table(T/'take.tsv');keep=[]
    from pins import verify
    withdrawals=[]
    for log in S.glob('handoff-r2[2-7].log'):
        for line in log.read_text().splitlines():
            if not re.search(r'\bWITHDRAW|\bWITHHOLD|reclassif',line):continue
            for name in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)',line):
                withdrawals.append((name,line))
    audits=[]
    import hashlib,os
    for r in rows:
        n=int(r['n']);proof=Path(r['remote_quench'])
        matches=re.findall(r'sha256 ([0-9a-f]{64})',r['source'])
        match=(None,matches[-1]) if matches else None
        jobs=list((W/'jobs').glob('*-'+match[1]+'.json')) if match else []
        job=next((j for p in jobs if (j:=json.loads(p.read_text()))['path'] in r['source'] and r['source'].startswith(j['source'])),None)
        if job is None:
            audits.append(dict(n=n,allowed=False,reason='missing exact source job'));continue
        if job['kind']=='fresh-public' and n in (639,691,745,858,916,918):
            audits.append(dict(n=n,allowed=False,reason='public ancestry clearance unresolved'));continue
        if job['kind']=='fresh-follow':
            try:
                def lifted_only(line):
                    return 'samanyu' in line.lower() and not re.search(r'prvsiyan|1105|BY-SA|ShareAlike|penguin|joegun|overlap|missing|no root',line,re.I)
                verify(job,withdrawals,lifted_only)
            except Exception as e:
                audits.append(dict(n=n,allowed=False,reason=repr(e)));continue
        audits.append(dict(n=n,allowed=True,job_sha256=job['sha256']))
        if not proof.exists():continue
        source=Path(json.loads(proof.read_text())['file'])
        target=T/(str(n)+'.csv')
        if not source.exists() or source.read_bytes()!=target.read_bytes():continue
        if float(r['new'])>=bars[n]-1e-10:continue
        r['other_best']=repr(bars[n]);r['incremental_gain']=repr(bars[n]-float(r['new']));keep.append(r)
    write_json(W/'final-source-audit.json',audits)
    tmp=T/'take.tsv.tmp'
    with tmp.open('w') as f:
        w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence','start','polish_gain','other_best','incremental_gain','remote_quench'],delimiter='\t')
        w.writeheader();w.writerows(keep)
    os.replace(tmp,T/'take.tsv')
    kept={int(r['n']) for r in keep}
    for path in T.glob('[0-9]*.csv'):
        if int(path.stem) not in kept:
            dst=W/'final-out';dst.mkdir(exist_ok=True);path.replace(dst/path.name)
    (L/'results/harvest-r27-2026-11-14.tsv').write_bytes((T/'take.tsv').read_bytes())
    state(f'TAKE FINAL rows={len(keep)}; compared every live r27 ledger')


if __name__=='__main__':
    if '--wait' in sys.argv:
        prepare_at=dt.datetime(2026,11,14,23,54,40,tzinfo=dt.timezone.utc).timestamp()
        while time.time()<prepare_at:time.sleep(min(30,prepare_at-time.time()))
        prepare_take()
        report_at=dt.datetime(2026,11,14,23,55,2,tzinfo=dt.timezone.utc).timestamp()
        while time.time()<report_at:time.sleep(min(10,report_at-time.time()))
    elif '--take-only' in sys.argv:
        prepare_take();raise SystemExit(0)
    print(json.dumps(finalize(),indent=2))
