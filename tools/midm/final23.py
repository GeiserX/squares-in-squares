#!/usr/bin/env python3
"""Finish round 23 even if its interactive session ends. All search stops by 18:30Z."""
import csv
import datetime
import json
import hashlib
import re
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import round23 as r

STOP = 1794594300  # 18:25 UTC: leave five minutes for the last certified-file quench.
HARD = 1794594600
REPO = '$PRIVATE_REPO'


def stop_local():
    output = subprocess.check_output(['ps', '-Ao', 'pid=,ppid=,command='], text=True)
    ps = {}
    roots = set()
    for line in output.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) != 3:
            continue
        pid, parent, command = int(parts[0]), int(parts[1]), parts[2]
        ps[pid] = parent
        argv = command.split()
        module = str(r.L / 'tools/midm/round23.py')
        monitor = str(r.W / 'monitor.py')
        if (len(argv) in (3,4) and 'python' in Path(argv[0]).name.lower() and argv[-2] == module and argv[-1] in ('loop-snap', 'loop-collect')) or (len(argv) == 2 and argv[1] == monitor):
            roots.add(pid)
    while True:
        new = {pid for pid, parent in ps.items() if parent in roots} - roots
        if not new:
            break
        roots |= new
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in roots:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(0.2)
    r.state('STOP local snapshot, collector and monitor trees: %s' % sorted(roots))


def remote_stop():
    code = '''import os,subprocess,signal,time,pathlib
D=pathlib.Path.home()/'scratch/squares-midm'
roots=set(map(int,(D/'workers.pids').read_text().split()))
ps={}
for l in subprocess.check_output(['ps','-Ao','pid=,ppid='],text=True).splitlines():
 a,b=map(int,l.split());ps[a]=b
while True:
 new={p for p,q in ps.items() if q in roots}-roots
 if not new:break
 roots|=new
for sig in (signal.SIGTERM,signal.SIGKILL):
 for p in roots:
  try:os.kill(p,sig)
  except ProcessLookupError:pass
 time.sleep(.2)
print('stopped own remote tree',sorted(roots))
'''
    r.run(['ssh', 'boxE', '$SCRATCH/squares-base/venv/bin/python', '-'], input=code, text=True)


def last_collect():
    # There are no kick workers now. Quench pending certified files on the free first slot.
    for _ in range(4):
        r.collect(final=True)
        if not (r.W / 'fq-pending.json').exists():
            return
        left = int(HARD - time.time() - 5)
        if left <= 0:
            break
        code = '''import pathlib,subprocess,os,signal,sys,time
D=pathlib.Path.home()/'scratch/squares-midm';os.chdir(D)
if (D/'fqout/DONE').exists():sys.exit(0)
if time.time()>=1794594598:sys.exit(3)
with open('logs/final-quench.log','a') as out:
 p=subprocess.Popen(['nice','-n','5',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'),'midm_fqonce.py','fqin','fqout',str(pathlib.Path.home()/'scratch/squares-base/fq'),'x'],stdout=out,stderr=subprocess.STDOUT,start_new_session=True)
 try:rc=p.wait(timeout=max(1,min(%d,1794594600-time.time()-1)))
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);p.wait();sys.exit(3)
if rc==0:(D/'fqout/DONE').touch()
sys.exit(rc)
''' % left
        result = subprocess.run(['ssh', 'boxE', '$SCRATCH/squares-base/venv/bin/python', '-'], input=code, text=True)
        if result.returncode:
            r.state('STOP final quench at hard deadline; drain completed files and withhold unfinished inputs')
            r.collect(final=True)
            break
    # A timed-out batch is withheld. Existing fq rows remain available.
    r.certify([r.W / 'raw-fq'], r.T)
    r.handoff()


def git_run(args):
    cmd = ['git'] + args
    for attempt in range(2):
        result = subprocess.run(cmd, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print(result.stdout, end='', flush=True)
        if result.returncode == 0:
            return
        if attempt == 0 and 'index.lock' in result.stdout:
            time.sleep(3)
            continue
        result.check_returncode()


def text_output(args):
    return subprocess.check_output(args, text=True, cwd=REPO).strip()


def audit_sources():
    tags=dict(line.split('\t')[:2] for line in (r.W/'TAGS.tsv').read_text().splitlines())
    take=r.rows(r.T/'take.tsv')
    for row in take:
        n=int(row['n']);key=int(re.search(r'@run_s(\d+)',tags[str(n)])[1])
        table={int(x['n']):x for x in r.rows(r.W/('r%d.tsv'%key))}
        actual=r.packing_score((r.W/('r%d'%key)/('%d.csv'%n)).read_bytes(),n)
        declared=float(table[n]['score'])
        if abs(actual-declared)>=5e-11 or not float(row['new'])<min(actual,declared)-1e-10:
            raise RuntimeError('published start-score audit failed for n%d'%n)
    r.state('CONTROL final source audit passed for%d published rows: literal start scores and source tables match, each result improves its actual start by>1e-10.'%len(take))


def finish():
    stop_local()
    remote_stop()
    last_collect()
    audit_sources()
    r.run(['rsync','-a',r.REMOTE,str(r.W/'boxE-final')+'/'])
    check=subprocess.check_output(['rsync','-ani','--checksum',r.REMOTE,str(r.W/'boxE-final')+'/'],text=True)
    if check.strip():raise RuntimeError('remote checksum mismatch: '+check)
    r.run(['ssh','boxE','rm -rf $SCRATCH/squares-midm'])
    for temporary in r.T.glob('.*.tmp'):
        temporary.unlink()
    r.state('FINISH boxE files copied, checksum verified and scratch removed; all workers stopped')
    while time.time() < 1794595140:
        time.sleep(min(30,1794595140-time.time()))
    publish_report()


def resume_raw_job(job, archive):
    result=dict(job)
    source=archive/job['sub']
    if not source.exists():source=r.W/job['sub']
    try:
        payload=source.read_bytes()
    except OSError:
        return result
    result.update(input_local=str(source),input_sha256=hashlib.sha256(payload).hexdigest())
    options=[]
    for path in (archive/('run/s%d/raw'%job['k'])).glob('%d-*-%d-*.csv'%(job['n'],job['seed'])):
        try:options.append((r.packing_score(path.read_bytes(),job['n']),path))
        except (OSError,KeyError,ValueError):continue
    if options:
        try:original=r.packing_score(payload,job['n'])
        except (KeyError,ValueError):return result
        score,path=min(options,key=lambda x:(x[0],str(x[1])))
        result.update(resume_sub=str(path),resume_seed=job['seed']+100,resume_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),resume_score_before_cert=score,partial_gain_before_cert=max(0.,original-score))
    return result


def publish_report():
    cutoff=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
    table=r.L/'results/midm-r23-2026-11-13.tsv'
    if '--preflight' in sys.argv:
        table=r.W/'report-results-preview.tsv'
    sums=json.loads(text_output([r.PY,str(r.L/'tools/midm/table23.py'),str(table)]))
    take=r.rows(r.T/'take.tsv')
    done=[json.loads(p.read_text()) for p in (r.W/'boxE-final/done').glob('*.json')]
    groups={}
    for j in done:
        key='raw legs' if j.get('leg') else ('public' if j.get('public') else ('new-design raw' if j.get('raw_design') else j['source'][-3:]))
        g=groups.setdefault(key,dict(scans=0,seconds=0.,gain_before_cert=0.,finds=0))
        g['scans']+=1;g['seconds']+=j.get('elapsed',0);g['gain_before_cert']+=j.get('gain',0);g['finds']+=j.get('finds',0)
    pending_jobs=[]
    jobpaths={path.name:path for path in (r.W/'jobs').glob('*.json')}
    jobpaths.update({path.name:path for path in (r.W/'boxE-final/jobs').glob('*.json')})
    for name,jobpath in jobpaths.items():
        if (r.W/'boxE-final/done'/name).exists():continue
        if (r.W/'boxE-final/cancel'/jobpath.stem).exists() or (r.W/'cancel'/jobpath.stem).exists():continue
        pending_jobs.append(resume_raw_job(dict(json.loads(jobpath.read_text()),job_file=name),r.W/'boxE-final'))
    r.atomic(r.W/'pending-final.json',json.dumps(pending_jobs,indent=2)+'\n')
    partial_finds=[j for j in pending_jobs if j.get('partial_gain_before_cert',0)>=1e-6]
    owed_results=[dict(n=j['n'],gain=j.get('gain',0),seconds=j.get('elapsed',0)) for j in done if j.get('owed_leg')]
    public_jobs=[json.loads(p.read_text()) for p in (r.W/'jobs').glob('*.json') if json.loads(p.read_text()).get('public')]
    complete={j['k'] for j in done if not j.get('leg')}
    pending=[j['n'] for j in public_jobs if j['k'] not in complete]
    r.atomic(r.W/'public-pending.tsv','n\n'+''.join(str(n)+'\n' for n in pending))
    immediate=sum(float(x['start'])-float(x['new']) for x in take)
    qgain=sum(float(x.get('polish_gain',0)) for x in take)
    measurements=[
      'Old 370 control: six kicks, one find, side 19.756747264363 to 19.756683828751, gain 3.298e-6.',
      'The source capture control matched public 639, rejected a stale score and incomplete CSV, and checked 66 current rows with zero deferrals.',
      'Queue controls passed for newest-first order, reserved public slot and claims. The certifier rejected frozen 639 and accepted improved 639.',
      'Per-file completion control accepted the exact input and rejected absent and changed-input markers. The live 587 quench drained separately from 639.',
      'Completed jobs with nonzero return codes: '+json.dumps([dict(n=j['n'],k=j['k'],returncode=j.get('returncode')) for j in done if j.get('returncode',0)!=0],sort_keys=True),
      'The interrupted-resume control recovered the best raw 264 point, gain 5.16389e-6 and its digest. Another seed returned no saved point.',
      '%d completed jobs. Groups: %s'%(len(done),json.dumps(groups,sort_keys=True)),
      'Take: %d rows, %.12g below round21; %d rows below all frozen r22 and other live r23 takes, gain %.12g.'%(sums['rows'],sums['gain_round21'],sums['live_rows'],sums['gain_all']),
      'Every published row passed floatsafe at 2.2e-11, received an fq quench from that certified file on boxE, and passed certification again.',
      'Margin over exact source rows %.12g; certified-file quench margin %.12g.'%(immediate,qgain),
      'Public initial scans %d of %d, unfinished n %s.'%(sum(j.get('public',False) and not j.get('leg') for j in done),len(public_jobs),pending),
      'Productive interrupted raw finds: '+json.dumps([dict(n=j['n'],gain=j['partial_gain_before_cert'],resume_sub=j['resume_sub']) for j in partial_finds],sort_keys=True),
      'Owed raw leg outcomes: '+json.dumps(owed_results,sort_keys=True),
      'Frozen backlog outcomes: '+json.dumps([dict(n=j['n'],gain=j.get('gain',0),seconds=j.get('elapsed',0)) for j in done if j.get('backlog') and not j.get('leg')],sort_keys=True),
      'The public queue control placed 692 before newer 989. The initial 639 source gained 2.30315e-4 in 150 seconds.',
      'The shared deadline guard stopped a simulated blocked child in 0.103 seconds. Both scan and certified-file quench calls bound their timeout by that deadline.',
      'The allocation audit found three reused keys after controller restarts. None affected a published row. Two unstarted interior components were quarantined; the allocator now skips existing source directories and tables.',
      'Comparison time '+cutoff+'. boxE scratch copy passed checksum comparison before removal.'
    ]
    next_items=[]
    owed=sorted({j['n'] for j in pending_jobs if j.get('owed_leg')})
    backlog=sorted({j['n'] for j in pending_jobs if j.get('backlog')})
    if (r.W/'fq-pending.json').exists():
        next_items.append('Finish the withheld inputs in work/fq-send. The required certified-file quench reached the common deadline.')
        measurements.append('A partial quench batch remains withheld. Every completed file was drained separately.')
    for key,g in sorted(groups.items(),key=lambda x: -x[1]['gain_before_cert']/max(1,x[1]['seconds'])):
        lead={'public':('Finish the %d public layouts in work/public-pending.tsv.'%len(pending) if pending else 'Kick fresh public layouts first.'),
              'raw legs':'Continue raw legs while they gain 1e-6 or more.',
              'r23':'Give fresh builds priority over older source versions.',
              'r22':'Test pending frozen inputs when fresh builds are quiet.',
              'r20':'Test remaining frozen layouts '+str(backlog)+' from work/pending-final.json.',
              'new-design raw':'Test a new geometry before repeating the raw near starts.'}.get(key,'Test new '+key+' inputs.')
        if key=='r20' and not backlog:
            lead='Require a changed layout before repeating this frozen backlog.' if g['gain_before_cert']<1e-6 else 'Test fresh builds from these families.'
        line=lead+' %d scans gained %.6g before certification in %.1f seconds.'%(g['scans'],g['gain_before_cert'],g['seconds'])
        if key=='r20':line+=' The round 21 backlog 869 scan gained 6.7e-5.'
        next_items.append(line)
        if key=='raw legs' and partial_finds:
            next_items.append('Continue interrupted raw finds '+str([(j['n'],float('%.6g'%j['partial_gain_before_cert'])) for j in partial_finds])+' from work/pending-final.json using resume_sub. Each listed gain exceeds 1e-6 before certification.')
    if owed:
        next_items.append('Recheck old owed legs '+str(owed)+' against the latest bar. The %d tested owed legs gained %.6g in %.1f seconds.'%(len(owed_results),sum(j['gain'] for j in owed_results),sum(j['seconds'] for j in owed_results)))
    if backlog and 'r20' not in groups:
        next_items.append('Reserve a window for frozen backlog '+str(backlog)+'. The round 21 backlog 869 scan gained 6.7e-5. Starts are in work/pending-final.json.')
    measurements.append('Unstarted or interrupted jobs saved in work/pending-final.json: '+str(len(pending_jobs))+'. Owed raw n '+str(owed)+', frozen backlog n '+str(backlog)+'.')
    next_items.append('Require a geometry change before repeating old near layouts. Round 20 had zero certified wins from 17 starts.')
    text=['## 14. Round 23 (2026-11-13)','','Two boxE slots ran until 18:25Z. Search and final quenches shared the 18:30Z deadline.',
          'One slot served the 39 public layouts left by round 22 from the start.',
          'New forensics layouts led the other slot. Useful raw legs and other fresh starts followed.','',
          'Reserved windows served old raw legs and the frozen backlog.',
          'A later reorder put short public scans first. Each duration tier kept the newest file first.','',
          'The queue read takes and handoffs each minute. It inventoried near folders every ten minutes.',
          'Snapshots kept the exact bytes they hashed. Certified source files could not be newer than their take table.',
          'Source scores had to match the captured packing within 5e-11.','',
          'The old 370 control made six tries and found once. Its side fell from 19.756747264363 to 19.756683828751.',
          'Completion records name each certified input by its hash. The controls accepted the exact input and rejected stale records.',
          'The deadline guard stopped a simulated blocked child in 0.103 seconds.',
          'The collector drained each finished quench separately, including files from an unfinished batch.','',
          'Every published file passed floatsafe at 2.2e-11, then received an fq quench on boxE and passed certification again.','',
          'At '+cutoff+', %d rows were %.9g below round 21.'%(sums['rows'],sums['gain_round21']),
          '%d rows beat every frozen round 22 and other live round 23 take, by %.9g in total.'%(sums['live_rows'],sums['gain_all']),
          'The [results table](../results/midm-r23-2026-11-13.tsv) records both comparisons.','',
          '| n | gain on round 21 | gain on every take | start |','|---|---|---|---|']
    for row in r.rows(table):text.append('| %s | %.6g | %.6g | `%s` |'%(row['n'],float(row['gain_on_round21_file']),float(row['gain_on_all']),row['start_dir']))
    text+=['','| queue | scans | seconds | gain before certification |','|---|---|---|---|']
    for key,g in groups.items():text.append('| %s | %d | %.1f | %.6g |'%(key,g['scans'],g['seconds'],g['gain_before_cert']))
    text+=['','The exact source rows account for the inherited gains.',
           'The final take added %.9g beyond those rows. The certified-file quenches added %.9g.'%(immediate,qgain),
           'boxE copy passed a checksum check. All lane processes stopped, and its scratch was removed.','','Next round:','']
    text += [str(i)+'. '+line for i,line in enumerate(next_items,1)]
    section='\n'.join(text)+'\n'
    draft=r.W/'doc23-final.md';draft.write_text(('Draft preview from an active run. Finalization and cleanup have not run.\n\n' if '--preflight' in sys.argv else '')+section)
    r.run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(draft)])
    if '--preflight' in sys.argv:
        print('report render and readable control passed');return
    doc=r.L/'avenues/midm.md';content=doc.read_text()
    if '## 14. Round 23 ' not in content:doc.write_text(content.replace('\n## Summary\n','\n'+section+'\n## Summary\n',1))
    paths=['lanes/squares/avenues/midm.md','lanes/squares/results/midm-r23-2026-11-13.tsv',
           'lanes/squares/tools/midm/round23.py','lanes/squares/tools/midm/worker23.py',
           'lanes/squares/tools/midm/final23.py','lanes/squares/tools/midm/table23.py','lanes/squares/midm_take.py','lanes/squares/midm_fqonce.py','lanes/squares/midm_scan.py']
    git_run(['add']+paths)
    git_run(['commit','-m','feat(squares): run round 23 midm kick queues','--only','--']+paths)
    commit=text_output(['git','log','-1','--format=%H','--','lanes/squares/results/midm-r23-2026-11-13.tsv'])
    git_run(['show','--stat','--oneline',commit])
    committed=set(text_output(['git','show','--pretty=','--name-only',commit]).splitlines())
    if not committed.issubset(set(paths)):
        raise RuntimeError('commit contains unexpected paths: '+str(sorted(committed-set(paths))))
    body=text_output(['git','show','-s','--format=%B',commit])
    if body != 'feat(squares): run round 23 midm kick queues':
        raise RuntimeError('commit message changed unexpectedly')
    push='pushed'
    try:
        git_run(['pull','--rebase','--autostash']);git_run(['push','origin','HEAD:main'])
    except subprocess.CalledProcessError:
        if subprocess.run(['git','push','origin','HEAD:main'],cwd=REPO).returncode:push='not pushed'
    commit=text_output(['git','log','-1','--format=%H','--','lanes/squares/results/midm-r23-2026-11-13.tsv'])
    report=dict(lane='midm',improved_n=sums['rows'],gain=dict(against_round21=sums['gain_round21'],against_frozen_r22_and_other_live_r23=sums['gain_all'],live_improved_n=sums['live_rows']),take_dir=str(r.T),
                summary='Round 23 used two boxE slots. Every published result received a certified-file quench. Comparison '+cutoff+'. '+push+'.',
                what_was_measured=measurements,next=next_items,commits=[commit],processes_left='None. boxE workers and local loops stopped. boxE scratch copied, checksum verified, and removed.',blocked='nothing' if push=='pushed' else 'not pushed',repo='private repo',branch='main',worktree=REPO,pr='none')
    r.atomic(r.T/'report.json',json.dumps(report,indent=2)+'\n')
    r.state('FINISH take and report.json final; commit '+commit+' '+push)


def main():
    r.state('START finalizer pid=%d wait18:25Z hard deadline18:30Z log=work/final23.log'%os.getpid())
    while time.time()<STOP:time.sleep(min(30,STOP-time.time()))
    if '--now' not in sys.argv:
        os.execv(r.PY,[r.PY,str(Path(__file__).resolve()),'--now'])
    finish()

if __name__=='__main__':main()
