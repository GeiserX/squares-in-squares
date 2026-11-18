#!/usr/bin/env python3
"""Stop the round 24 lane, retain pending starts and write its measured report."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
import round24 as r

REPO='$PRIVATE_REPO'


def stop():
    out=subprocess.check_output(['ps','-Ao','pid=,ppid=,command='],text=True)
    ps={};roots=set()
    for line in out.splitlines():
        a=line.strip().split(None,2)
        if len(a)!=3:continue
        pid,parent,cmd=int(a[0]),int(a[1]),a[2];ps[pid]=parent
        if str(r.L/'tools/midm/round24.py') in cmd or 'lanes/squares/tools/midm/round24.py loop-' in cmd:roots.add(pid)
    while True:
        new={p for p,q in ps.items() if q in roots}-roots
        if not new:break
        roots|=new
    for sig in (signal.SIGTERM,signal.SIGKILL):
        for pid in roots:
            try:os.kill(pid,sig)
            except ProcessLookupError:pass
        time.sleep(.2)
    code="""import os,pathlib,signal,subprocess,time
D=pathlib.Path.home()/'scratch/squares-midm'
roots=set(map(int,(D/'workers.pids').read_text().split()));ps={}
for line in subprocess.check_output(['ps','-Ao','pid=,ppid='],text=True).splitlines():
 a,b=map(int,line.split());ps[a]=b
while True:
 new={p for p,q in ps.items() if q in roots}-roots
 if not new:break
 roots|=new
for sig in (signal.SIGTERM,signal.SIGKILL):
 for pid in roots:
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 time.sleep(.2)
print('stopped own remote tree',sorted(roots))
"""
    r.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python','-'],input=code,text=True)
    r.state('STOP all local round24 loops and both own boxE worker trees at common deadline22:15Z')


def audit_sources():
    tags=dict(line.split('\t')[:2] for line in (r.W/'TAGS.tsv').read_text().splitlines())
    for row in r.rows(r.T/'take.tsv'):
        n=int(row['n']);key=int(re.search(r'@run_s(\d+)',tags[str(n)])[1])
        tab=r.rows(r.W/('r%d.tsv'%key))[0]
        actual=r.packing_score((r.W/('r%d'%key)/('%d.csv'%n)).read_bytes(),n)
        assert abs(actual-float(tab['score']))<5e-11
        assert float(row['new'])<actual-1e-10
        assert r.clean_declared(row['source']+' '+row['licence'])
        proof=r.captured_proof(tab['source'])
        if proof:
            digest=hashlib.sha256((r.W/('r%d'%key)/('%d.csv'%n)).read_bytes()).hexdigest()
            assert Path(proof).name.startswith(digest), 'source proof digest mismatch n%d'%n
    r.state('CONTROL final audit: every row improves its exact immutable start; declared source chains exclude forbidden roots')


def finish():
    stop()
    # Drain only completed quenches. New work cannot start after the common end.
    r.collect(final=True)
    r.certify([r.W/'raw-fq'],r.T);r.handoff();audit_sources()
    archive=r.W/'boxE-final';r.run(['rsync','-a',r.REMOTE,str(archive)+'/'])
    check=subprocess.check_output(['rsync','-ani','--checksum',r.REMOTE,str(archive)+'/'],text=True)
    if check.strip():raise RuntimeError('remote checksum mismatch: '+check)
    r.run(['ssh','boxE','rm -rf $SCRATCH/squares-midm'])
    for temporary in r.T.glob('.*.tmp'):temporary.unlink()
    r.state('FINISH boxE archive checksum verified, scratch removed, all own workers stopped')
    r.state('WAIT final live-take comparison until22:24Z; take already final and remote workers stopped')
    comparison=1794608640  # 2026-11-13 22:24 UTC
    while time.time()<comparison:time.sleep(min(30,comparison-time.time()))
    report()


def git_run(args):
    for attempt in range(2):
        p=subprocess.run(['git']+args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(p.stdout,end='',flush=True)
        if not p.returncode:return p.stdout.strip()
        if attempt==0 and 'index.lock' in p.stdout:time.sleep(3);continue
        p.check_returncode()


def report():
    cutoff=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    preview='--preflight' in sys.argv
    table=(r.W/'report-preview.tsv') if preview else r.L/'results/midm-r24-2026-11-13.tsv'
    sums=json.loads(subprocess.check_output([r.PY,str(r.L/'tools/midm/table24.py'),str(table)],text=True))
    take=r.rows(r.T/'take.tsv');archive=r.W/('boxE' if preview else 'boxE-final')
    done=[json.loads(p.read_text()) for p in (archive/'done').glob('*.json')]
    groups={}
    for j in done:
        key='raw legs' if j.get('leg') else ('public' if j.get('public') else ('new-design raw' if j.get('raw_design') else j.get('source_kind','fresh r24')))
        g=groups.setdefault(key,dict(scans=0,seconds=0.,gain_before_cert=0.,finds=0))
        g['scans']+=1;g['seconds']+=j.get('elapsed',0);g['gain_before_cert']+=j.get('gain',0);g['finds']+=j.get('finds',0)
    pending=[];paths={p.name:p for p in (r.W/'jobs').glob('*.json')};paths.update({p.name:p for p in (archive/'jobs').glob('*.json')})
    for name,p in paths.items():
        if (archive/'done'/name).exists() or (archive/'cancel'/p.stem).exists() or (r.W/'cancel'/p.stem).exists():continue
        j=json.loads(p.read_text());f=archive/j['sub']
        if not f.exists():f=r.W/j['sub']
        if f.exists():j.update(input_local=str(f),input_sha256=hashlib.sha256(f.read_bytes()).hexdigest())
        j['job_file']=name
        options=[]
        for raw in (archive/('run/s%d/raw'%j['k'])).glob('%d-*-%d-*.csv'%(j['n'],j['seed'])):
            try:options.append((r.packing_score(raw.read_bytes(),j['n']),raw))
            except (OSError,ValueError,KeyError):continue
        if options and f.exists():
            score,raw=min(options,key=lambda x:x[0])
            original=r.packing_score(f.read_bytes(),j['n'])
            j.update(resume_sub=str(raw),resume_seed=j['seed']+100,resume_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),resume_score_before_cert=score,partial_gain_before_cert=max(0.,original-score))
        pending.append(j)
    r.atomic(r.W/('pending-preview.json' if preview else 'pending-final.json'),json.dumps(pending,indent=2)+'\n')
    measurements=[
        'Old 370 control: six kicks, one find, side 19.756747264363 to 19.756683828751, gain 3.298e-6.',
        'The ancestry-bar control accepted a legal n2 grid against0.5 for an own source and rejected it against0.4 for seed365 ancestry. A lower Samanyu live row did not mask the free alternative.',
        'The main session held 20 Samanyu-descended candidate rows. Samanyu-free rows of those counts use the round22 bar; other rows retain the original candidate bar.',
        'Every licence cell states Samanyu ancestry. Explicit seed counts are required for a positive Samanyu label; unresolved counts are withheld.',
        'Source-width control first passed a short source and failed at the old CSV limit. After the fix it retained all 536378 characters.',
        'Geometry control matched translated and rotated copies and kept an equal-side layout with a .15 center move distinct.',
        'Source control accepted the clean candidate and changed-count r23 n735. It rejected banned r23 n639, forbidden upstream datasets and missing provenance.',
        '%d completed scans. Groups: %s'%(len(done),json.dumps(groups,sort_keys=True)),
        'The source-proof audit repaired 15 links using exact input hashes and archived producer records. It withheld 38 unresolved starts; published rows passed the input-proof audit.',
        'Capture control accepted exact bytes and refused changed or missing points. New evidence filenames bind coordinate and metadata digests.',
        'Source withdrawals canceled queued starts and quarantined their raw descendants. Fresh public snapshots used the audited producer manifests.',
        'Completed scan failures: '+json.dumps([dict(n=j['n'],k=j['k'],returncode=j['returncode']) for j in done if j.get('returncode',0)]),
        'Take: %d rows, gain %.12g against round23 candidate; %d beat all other live r24 takes, gain %.12g.'%(sums['rows'],sums['gain_round23'],sums['live_rows'],sums['gain_all']),
        'Every published row passed floatsafe at 2.2e-11, received an fq quench from its certified file on boxE, and passed certification again.',
        'Margin beyond exact source rows %.12g; certified-file quench margin %.12g.'%(sum(float(x['start'])-float(x['new']) for x in take),sum(float(x.get('polish_gain',0)) for x in take)),
        'Round20 backlog and disallowed source chains stayed closed. Owed n981 was excluded because it descends from banned n801.',
        'Unstarted or interrupted jobs saved in work/pending-final.json: %d.'%len(pending),
        'Comparison '+cutoff+'. boxE archive passed checksum comparison before removal.'
    ]
    next_items=[]
    partial=[j for j in pending if j.get('partial_gain_before_cert',0)>=1e-6]
    if partial:
        measurements.append('Productive interrupted raw finds: '+json.dumps([dict(n=j['n'],gain=j['partial_gain_before_cert'],resume_sub=j['resume_sub']) for j in partial]))
        next_items.append('Resume interrupted raw finds from work/pending-final.json. Their measured partial gains exceed 1e-6 before certification.')
    if (r.W/'fq-pending.json').exists():
        measurements.append('Unfinished certified-input quenches remain withheld at the common deadline. Completed inputs were drained separately.')
        next_items.append('Finish withheld certified-input quenches in work/fq-send before publication. Their required quenches did not complete by the common deadline.')
    for key,g in sorted(groups.items(),key=lambda x:-x[1]['gain_before_cert']/max(1,x[1]['seconds'])):
        lead={'public':'Kick fresh public layouts first.','raw legs':'Continue raw legs while they gain 1e-6 or more.','fresh r24':'Kick fresh builds at handoff.','new-design raw':'Test fresh near geometry once.','accepted r23 unstarted':'Use clean unstarted builds only when fresh queues are empty.'}.get(key,'Recheck owed raw legs against the latest bar.')
        next_items.append(lead+' %d scans gained %.6g before certification in %.1f seconds.'%(g['scans'],g['gain_before_cert'],g['seconds']))
    if (r.W/'source-proof-deferrals.json').exists():
        count=len(json.loads((r.W/'source-proof-deferrals.json').read_text()))
        next_items.append('Audit the %d starts in work/source-proof-deferrals.json before reuse. Their input-proof links remained unresolved, and they were withheld.'%count)
    next_items.append('Keep old near repeats and round20 backlog closed. Round20 had no certified wins from 17 near starts.')
    section=['## 15. Round 24 (2026-11-13)','','Two boxE slots served fresh public and construction layouts before clean unstarted round23 layouts.',
        'The new 639 uses candidate layouts 496 and 590. The new 918 uses candidate layouts 590 and 917.',
        'Raw-find legs started from saved raw layouts. The round20 backlog stayed closed.',
        'Source fields reached 536378 characters. The certifier and results reader now accept fields up to 16 MiB.',
        'The queues read handoffs each minute and inventoried near folders every ten minutes.',
        'Source admission imported `forensics_sources.trace` and saved evidence by input hash.',
        'The old 370 control found once in six kicks. Its side fell from 19.756747264363 to 19.756683828751.',
        'Source controls accepted the candidate and a clean round23 row. They rejected forbidden roots and missing provenance.',
        'Search and certified-file quenches shared the 22:15Z deadline. Every published row passed floatsafe at 2.2e-11 before and after its boxE quench.','',
        'At '+cutoff+', the take held %d rows. Their score gains sum to %.9g against the original round23 candidate.'%(sums['rows'],sums['gain_round23']),
        '%d rows beat every other live round24 take, by %.9g in total.'%(sums['live_rows'],sums['gain_all']),
        'The [results table](../results/midm-r24-2026-11-13.tsv) records both comparisons.','',
        '| queue | scans | seconds | gain before certification |','|---|---|---|---|']
    for key,g in groups.items():section.append('| %s | %d | %.1f | %.6g |'%(key,g['scans'],g['seconds'],g['gain_before_cert']))
    section+=['','All own workers stopped. boxE archive passed a checksum comparison before scratch removal.','','Next round:','']
    section += [str(i)+'. '+s for i,s in enumerate(next_items,1)]
    section='\n'.join(section)+'\n';draft=r.W/'doc24.md';draft.write_text(section)
    r.run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(draft)])
    if preview:
        print('CONTROL report rendering and readable check passed; no cleanup or git action ran',flush=True);return
    doc=r.L/'avenues/midm.md';text=doc.read_text();a=text.find('## 15. Round 24 ')
    if a<0:doc.write_text(text.replace('\n## Summary\n','\n'+section+'\n## Summary\n',1))
    paths=['lanes/squares/midm_take.py','lanes/squares/avenues/midm.md','lanes/squares/results/midm-r24-2026-11-13.tsv']+['lanes/squares/tools/midm/'+x for x in ('round24.py','worker24.py','table24.py','final24.py','order24.py','revoke24.py')]
    # --only prevents a concurrent lane's staged files from entering this commit.
    git_run(['add']+paths);git_run(['commit','--only','-m','feat(squares): run round 24 midm kick queues','--']+paths)
    commit=git_run(['log','-1','--format=%H','--','lanes/squares/results/midm-r24-2026-11-13.tsv']);git_run(['show','--stat','--oneline',commit])
    assert set(git_run(['show','--pretty=','--name-only',commit]).splitlines()).issubset(set(paths))
    push='pushed'
    try:git_run(['pull','--rebase','--autostash']);git_run(['push','origin','HEAD:main'])
    except subprocess.CalledProcessError:
        if subprocess.run(['git','push','origin','HEAD:main'],cwd=REPO).returncode:push='not pushed'
    commit=git_run(['log','-1','--format=%H','--','lanes/squares/results/midm-r24-2026-11-13.tsv'])
    obj=dict(lane='midm',improved_n=sums['rows'],gain=dict(against_round23_candidate=sums['gain_round23'],against_accepted_bars=sums['gain_accepted_bars'],beyond_other_live_r24=sums['gain_all'],live_improved_n=sums['live_rows']),take_dir=str(r.T),summary='Round24 used two boxE slots. All published rows received certified-file quenches. '+push+'.',what_was_measured=measurements,next=next_items,commits=[commit],processes_left='None. Own local loops and boxE workers stopped. boxE scratch copied, checksum verified and removed.',blocked='nothing' if push=='pushed' else 'not pushed',repo='private repo',branch='main',worktree=REPO,pr='none')
    r.atomic(r.T/'report.json',json.dumps(obj,indent=2)+'\n');r.state('FINISH report.json written; commit '+commit+' '+push)


if __name__=='__main__':
    if '--preflight' in sys.argv:
        report();sys.exit(0)
    r.state('START finalizer pid%d common deadline22:15Z log=work/final24.log'%os.getpid())
    if '--now' not in sys.argv:
        while time.time()<r.END:time.sleep(min(30,r.END-time.time()))
        os.execv(r.PY,[r.PY,str(Path(__file__).resolve()),'--now'])
    finish()
