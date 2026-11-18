#!/usr/bin/env python3
"""Finish round 25, retain measurements and publish the lane's report."""
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
import round25 as r
import sources25 as sources

REPO = str(r.L.parents[1])
OWN = ['lanes/squares/avenues/midm.md', 'lanes/squares/results/midm-r25-2026-11-14.tsv']
OWN += ['lanes/squares/tools/midm/'+x+'.py' for x in ('round25','worker25','sources25','revoke25','final25')]


def stop_local():
    roots = set(int(x) for x in (r.W/'local.pids').read_text().split())
    ps = {}
    for line in subprocess.check_output(['ps','-Ao','pid=,ppid=,command='], text=True).splitlines():
        fields = line.strip().split(None,2)
        if len(fields) == 3:
            ps[int(fields[0])] = (int(fields[1]), fields[2])
    roots = {pid for pid in roots if pid in ps and 'round25.py' in ps[pid][1]}
    while True:
        new = {pid for pid, (parent, cmd) in ps.items() if parent in roots}-roots
        if not new:
            break
        roots |= new
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in roots:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(.2)


def stop_remote():
    code = '''import os,pathlib,signal,subprocess,time
D=pathlib.Path.home()/'scratch/squares-midm'
roots=set(map(int,(D/'workers.pids').read_text().split())); ps={}
for line in subprocess.check_output(['ps','-Ao','pid=,ppid=,command='],text=True).splitlines():
 a=line.strip().split(None,2)
 if len(a)==3:ps[int(a[0])]=(int(a[1]),a[2])
roots={p for p in roots if p in ps and 'worker25.py' in ps[p][1]}
verified=set()
for pid in roots:
 try:
  cwd=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True,stderr=subprocess.DEVNULL)
  if 'n'+str(D.resolve()) in cwd.splitlines():verified.add(pid)
 except subprocess.CalledProcessError:pass
roots=verified
while True:
 new={p for p,(q,c) in ps.items() if q in roots}-roots
 if not new:break
 roots|=new
for sig in (signal.SIGTERM,signal.SIGKILL):
 for pid in roots:
  try:os.kill(pid,sig)
  except ProcessLookupError:pass
 time.sleep(.2)
print('stopped own remote tree',sorted(roots))
'''
    r.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python','-'], input=code, text=True)
    r.state('STOP both boxE worker trees and local loops; common deadline02:45Z')


def proof_audit(row, tags):
    n = int(row['n']); tag = tags[str(n)]
    key = int(re.search(r'@run_s(\d+)', tag)[1])
    table = r.rows(r.W/('r%d.tsv'%key))[0]
    point = r.W/('r%d'%key)/('%d.csv'%n)
    digest = hashlib.sha256(point.read_bytes()).hexdigest()
    actual = r.packing_score(point.read_bytes(), n)
    assert abs(actual-float(table['score'])) < 5e-11
    assert float(row['new']) < actual-1e-10
    proof = r.captured_proof(table['source'])
    assert proof and Path(proof).name.startswith(digest), 'unbound input proof'
    evidence = json.loads(Path(proof).read_text())
    for original, expected in evidence.get('linked_proof_sha256',{}).items():
        point=Path(evidence.get('linked_proof_snapshots',{}).get(original,original))
        assert hashlib.sha256(point.read_bytes()).hexdigest()==expected, 'retained parent proof changed'
    assert sources.audit_evidence(evidence)[0], 'forbidden frozen or held root'
    assert sources.referenced_proofs(evidence)[0], 'forbidden retained proof'
    assert sources.clean_text(row['source']+' '+row['licence'])
    return key


def finalize_take():
    r.update_base()
    r.certify([r.W/'raw-fq'], r.T)
    base = {int(x['n']):float(x['score']) for x in csv.DictReader((r.W/'base-details.csv').open())}
    peers = dict(base)
    for directory in r.B.glob('take-*-r25'):
        if directory == r.T:
            continue
        for row in r.rows(directory/'take.tsv'):
            if sources.clean_text(row.get('source','')+' '+row.get('licence','')):
                n = int(row['n']); peers[n] = min(peers[n],float(row['new']))
    tags = dict(line.split('\t')[:2] for line in (r.W/'TAGS.tsv').read_text().splitlines())
    keep = []; withdrawn = []
    for row in r.rows(r.T/'take.tsv'):
        n = int(row['n']); new = float(row['new'])
        try:
            proof_audit(row, tags)
        except (AssertionError, OSError, ValueError) as ex:
            withdrawn.append((n, str(ex))); continue
        if new >= min(base[n], peers[n])-1e-10:
            withdrawn.append((n, 'no longer below base and every live peer by1e-10')); continue
        row['held'] = repr(base[n]); row['gain'] = repr(base[n]-new); keep.append(row)
    cols = ('n','held','new','gain','source','licence','start','polish_gain')
    out = io.StringIO(); writer=csv.DictWriter(out,fieldnames=cols,delimiter='\t',extrasaction='ignore');writer.writeheader();writer.writerows(keep)
    r.atomic(r.T/'take.tsv',out.getvalue())
    for n, reason in withdrawn:
        (r.T/('%d.csv'%n)).unlink(missing_ok=True)
        r.state('DROP final n%d: %s'%(n, reason))
    for p in r.T.glob('*.csv'):
        if int(p.stem) not in {int(x['n']) for x in keep}:
            p.unlink()
    for temporary in r.T.glob('.*.tmp'):temporary.unlink(missing_ok=True)
    r.handoff()
    return keep, base, peers


def git(args):
    for attempt in range(2):
        p = subprocess.run(['git']+args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        print(p.stdout,end='',flush=True)
        if not p.returncode:
            return p.stdout.strip()
        if attempt == 0 and 'index.lock' in p.stdout:
            time.sleep(3); continue
        p.check_returncode()


def report(preview=False):
    keep, base, peers = finalize_take()
    archive = r.W/('boxE' if preview else 'boxE-final')
    done = [json.loads(p.read_text()) for p in (archive/'done').glob('*.json')]
    groups = {}
    revoked=set(json.loads((r.W/'revoked-keys.json').read_text())) if (r.W/'revoked-keys.json').exists() else set()
    for j in done:
        kind = 'raw legs' if j.get('leg') else ('fresh near' if j.get('raw_design') else j.get('source_kind','public' if j.get('public') else 'fresh r25'))
        excluded=j['k'] in revoked
        if excluded:kind='withdrawn source'
        g = groups.setdefault(kind,dict(scans=0,seconds=0.,gain_before_cert=0.,finds=0))
        g['scans'] += 1; g['seconds'] += j.get('elapsed',0);g['gain_before_cert'] += 0. if excluded else max(0.,j.get('gain',0));g['finds'] += j.get('finds',0)
    gain = sum(base[int(x['n'])]-float(x['new']) for x in keep)
    live = sum(min(base[int(x['n'])],peers[int(x['n'])])-float(x['new']) for x in keep)
    tags = dict(line.split('\t')[:2] for line in (r.W/'TAGS.tsv').read_text().splitlines())
    input_gains = {}
    for row in keep:
        n = int(row['n'])
        key = int(re.search(r'@run_s(\d+)', tags[str(n)])[1])
        start = float(r.rows(r.W/('r%d.tsv'%key))[0]['score'])
        input_gains[n] = dict(input_score=start, gain_on_input=start-float(row['new']))
    cols = ['n','held','new','gain_on_base','lowest_other','gain_on_all','input_score','gain_on_input','source','licence']
    buf=io.StringIO();writer=csv.DictWriter(buf,fieldnames=cols,delimiter='\t');writer.writeheader()
    for row in keep:
        n=int(row['n']);new=float(row['new'])
        writer.writerow(dict(n=n,held=base[n],new=new,gain_on_base=base[n]-new,lowest_other=peers[n],gain_on_all=min(base[n],peers[n])-new,source=row['source'],licence=row['licence'],**input_gains[n]))
    table = r.W/'report-preview.tsv' if preview else r.L/'results/midm-r25-2026-11-14.tsv'
    table.write_text(buf.getvalue())
    pending=[]
    for path in (archive/'jobs').glob('*.json'):
        j=json.loads(path.read_text())
        if j['k'] in revoked or (archive/'done'/path.name).exists() or (archive/'cancel'/path.stem).exists():continue
        point=archive/j['sub']
        if not point.is_file():continue
        j=dict(j,job_file=path.name,input_local=str(point),input_sha256=hashlib.sha256(point.read_bytes()).hexdigest(),source_table=str(r.W/('r%d.tsv'%j['k'])))
        pending.append(j)
    if not preview:r.atomic(r.W/'pending-final.json',json.dumps(pending))
    nexts=[]
    completed=set(json.loads((r.W/'fq-done.json').read_text())) if (r.W/'fq-done.json').exists() else set()
    sendtags=dict(line.split('\t')[:2] for line in (r.W/'fq-send/TAGS.tsv').read_text().splitlines()) if (r.W/'fq-send/TAGS.tsv').exists() else {}
    deferred=[]
    for point in (r.W/'fq-send').glob('*.csv'):
        match=re.search(r'@run_s(\d+)',sendtags.get(point.stem,''))
        if match and int(match[1]) not in revoked and hashlib.sha256(point.read_bytes()).hexdigest() not in completed:deferred.append(str(point))

    if deferred:
        nexts.append('Finish %d withheld certified-input quenches in work/fq-send. Their required quench missed the common deadline.'%len(deferred))
        if not preview:
            with (r.B/'handoff-r25.log').open('a') as out:
                out.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' midm -> quench: withheld certified-input quench files missed the common deadline; preserve for next round, '+str(r.W/'fq-send')+'\n')
    nexts.append('Kick fresh public and rebuilt designs before saved starts. Round24 fresh builds gained 0.000465172 in 33 scans. Its two public scans gained 6.81928e-5 in 342.5 seconds.')
    latest = {}
    for job in done:
        if job['k'] in revoked:
            continue
        if job['k'] not in latest or job.get('leg', 0) > latest[job['k']].get('leg', 0):
            latest[job['k']] = job
    for job in sorted(latest.values(), key=lambda j:j.get('gain', 0)/max(1,j.get('elapsed', 0)), reverse=True):
        if job.get('gain', 0) < 1e-6:
            continue
        near = sorted((r.T/'near').glob('%d-raw-kick-r%d-*.csv'%(job['n'],job['k'])))
        if near:
            nexts.append('Continue the raw leg for n%d from %s. Its last scan gained %.9g before certification in %.1f seconds. It still missed the live bar, and no further leg finished.'%(job['n'],near[-1],job['gain'],job['elapsed']))
    for name,g in sorted(groups.items(),key=lambda x: x[1]['gain_before_cert']/max(1,x[1]['seconds']),reverse=True):
        if name=='withdrawn source':continue
        nexts.append('%s: %d scans gained %.9g before certification in %.1f seconds. Prioritize changed, traced designs and continue raw legs only while they gain at least 1e-6.'%(name,g['scans'],g['gain_before_cert'],g['seconds']))
    if pending:nexts.append('Rerank %d unstarted clean inputs in work/pending-final.json against the next base. Fresh designs took the available slots, so these inputs have no completed scan.'%len(pending))
    nexts.append('Keep old near repeats and round 20 backlog closed. Round20 had 0 certified wins from 17 starts.')
    if not preview:
        doc='\n## 16. Round 25 (2026-11-13 to 14)\n\n'
        doc+='Two boxE slots served fresh public layouts and builds. New search starts stopped at 02:15Z. Search and certified-file quenches shared the 02:45Z deadline.\n'
        doc+='The unfinished round 24 quenches and 38 source-proof deferrals went to the quench lane. Two claimed, never-started public layouts ran while fresh queues were empty.\n'
        doc+='Source admission walked recorded parents and retained proof files. It saved each proof by its coordinate and metadata hashes. No retained row uses a forbidden or unresolved root.\n'
        doc+='The old 370 control made 31 tries and found once. Its side fell from 19.756747264363 to 19.756683828751. Source controls rejected the hidden GitHub 735 root and accepted the licensed held 370.\n'
        doc+='Withdrawals quarantined rebuilt 534 and held 975 descendants. Relative-parent controls retained public 542 and refused the missing old reader 974 link.\n'
        doc+='Owned-PID cancellation stopped its test tree in 0.735 seconds on boxE. Group signalling failed with EPERM and was removed.\n'
        doc+='The old 921 far-zone alias reaches the unlicensed 983 seed. Its inputs and four old near handoffs were quarantined. New near filenames bind the input key and coordinate hash.\n'
        doc+='Every retained take row passed floatsafe at 2.2e-11 before and after a certified-file quench on boxE. The final comparison dropped rows that no longer beat every live take.\n\n'
        doc+='The take holds %d rows. Gains sum to %.12g against the base and %.12g beyond other live takes. The [results table](../results/midm-r25-2026-11-14.tsv) records both comparisons.\n\n'%(len(keep),gain,live)
        doc+='These base gains include the input designs from other lanes. Our kicks and quenches gained %.12g against those exact inputs. The table records each input score.\n\n'%sum(v['gain_on_input'] for v in input_gains.values())
        doc+='| queue | scans | seconds | gain before certification |\n|---|---|---|---|\n'
        for name,g in groups.items():
            doc+='| %s | %d | %.1f | %.9g |\n'%(name,g['scans'],g['seconds'],g['gain_before_cert'])
        doc+='\nNext round:\n\n'+'\n'.join('%d. %s'%(i+1,x) for i,x in enumerate(nexts))+'\n'
        (r.W/'doc25.md').write_text(doc)
        check=['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(r.W/'doc25.md')]
        r.run(check)
        p=r.L/'avenues/midm.md'; old=p.read_text();p.write_text(old.split('\n## 16. Round 25')[0]+doc)
    eligible=[j for j in done if j['k'] not in revoked and j.get('gain',0)>0]
    best_scan=max(eligible,key=lambda j:j['gain']) if eligible else None
    measured = [
        'Retained rows against their exact captured inputs: '+json.dumps(input_gains,sort_keys=True)+'. Base gains also include the upstream designs.',
        '%d unstarted source-admitted jobs saved in work/pending-final.json.'%len(pending),
        'Base details '+str(r.W/'base-details.csv')+' SHA256 '+hashlib.sha256((r.W/'base-details.csv').read_bytes()).hexdigest()+'.',
        'Replacement control admitted the n=534 version with the approved hash and its exact recorded descendants. It refused old n=172 and mixed old/new parent trees.',
        'Comparison at '+time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'. Withdrawn-source scans are recorded separately and supply no eligible gain.',
        'Old 370 control: 31 tries, 1 find, side 19.756747264363 to 19.756683828751 in 36 seconds.',
        'Source controls accepted licensed samanyu1808 and held 370, and rejected banned datasets, explicit seed flags and the hidden GitHub 735 root.',
        'Base control: legal n=2 grid accepted against 0.5 and rejected against 0.4. Geometry control matched translations and turns and kept a 0.15 center move distinct. All three tolerances left 10 representatives of 20 n=985 inputs.',
        'Relative-parent control retained public n=542 and refused the missing old reader n=974 source link under n=975. Source withdrawals quarantined rebuilt n=534 and held n=975 descendants before publication.',
        'Cancellation controls stopped an owned parent and its child in 0.877 seconds locally and 0.735 seconds on boxE. Group signalling failed with EPERM and was removed.',
        'Immutable-proof control retained a captured own-grid parent after its live metadata changed, and refused the changed seed parent without a snapshot.',
        'The n=921 far-zone audit rejected 190 matching input versions and withdrew four old raw near handoffs. All retained take rows passed the separate root audit. New near filenames bind input key and coordinate hash.',
        'Queue control ranked fresh n=534 before unseen near n=650 and repeated-count near n=985.',
        'Largest eligible scan before certification: '+json.dumps({k:best_scan[k] for k in ('k','n','gain','elapsed','source') if k in best_scan} if best_scan else {}),
        'Withdrawal parser control retained a clean parent described as equal to a withdrawn historical floor and held explicit WITHDRAW/WITHHOLD inputs. Source audits restored n=735,790,968.',
        'Completed scans by group: '+json.dumps(groups,sort_keys=True),
        'All retained take rows passed floatsafe at 2.2e-11, received a quench from that certified file on boxE, then passed certification and full-parent ancestry audit again.',
        'Final rows must beat the current base and every other live round 25 take by more than 1e-10.',
        'The frozen round 24 fq-send and 38 source-proof deferrals were assigned to quench. Old near repeats and round 20 backlog stayed closed.',
    ]
    commits=[];push='not pushed'
    if not preview:
        git(['add','--']+OWN)
        git(['commit','--only','-m','Measure round 25 midm kicks and retain source proofs','--']+OWN)
        commit=git(['rev-parse','HEAD']);commits=[commit]
        names=set(git(['show','--pretty=','--name-only',commit]).splitlines())
        assert names <= set(OWN), 'commit includes another lane'
        git(['show','--stat','--oneline',commit])
        for attempt in range(2):
            pulled=False
            try:
                git(['pull','--rebase','--autostash']);pulled=True
                actual=git(['log','-1','--format=%H','--','lanes/squares/tools/midm/round25.py'])
                names=set(git(['show','--pretty=','--name-only',actual]).splitlines())
                assert names <= set(OWN), 'rebased commit includes another lane'
                git(['show','--stat','--oneline',actual]);commits=[actual]
                git(['push','origin','HEAD:main']);push='pushed';break
            except subprocess.CalledProcessError:
                if not pulled:
                    try:
                        actual=git(['log','-1','--format=%H','--','lanes/squares/tools/midm/round25.py'])
                        if actual:
                            git(['show','--stat','--oneline',actual])
                            git(['push','origin','HEAD:main']);commits=[actual];push='pushed';break
                    except subprocess.CalledProcessError:pass
                if attempt==0:time.sleep(3)
        if push!='pushed':
            commits=[git(['log','-1','--format=%H','--','lanes/squares/tools/midm/round25.py'])]
    result=dict(lane='midm',improved_n=len(keep),gain=dict(against_base=gain,beyond_other_live_r25=live),take_dir=str(r.T),summary='%d certified rows retained after source and live-peer audits; %d boxE scans; %s.'%(len(keep),len(done),push),what_was_measured=measured,next=nexts,commits=commits,processes_left='None. Own local loops and both boxE worker trees stopped; remote archive checksum verified and scratch removed.' if not preview else 'Preview: workers remain active.',blocked='nothing',repo='private repo',branch='main',worktree=REPO,pr='none')
    r.atomic(r.W/'report-preview.json' if preview else r.T/'report.json',json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


def main():
    if '--preview' in sys.argv:
        report(True);return
    watched = [Path(__file__).resolve()]+[Path(__file__).parent/(name+'.py') for name in ('round25','sources25','revoke25','worker25')]
    loaded = {str(path):path.stat().st_mtime_ns for path in watched}
    while time.time() < r.END:
        if {str(path):path.stat().st_mtime_ns for path in watched} != loaded:
            os.execv(r.PY,[r.PY,str(Path(__file__).resolve())]+sys.argv[1:])
        time.sleep(min(30,r.END-time.time()))
    stop_local();stop_remote();r.collect(final=True)
    archive = r.W/'boxE-final'
    r.run(['rsync','-a',r.REMOTE,str(archive)+'/'])
    differences=subprocess.check_output(['rsync','-ani','--checksum',r.REMOTE,str(archive)+'/'],text=True)
    assert not differences.strip(), differences
    r.run(['ssh','boxE','rm -rf $SCRATCH/squares-midm'])
    (r.W/'REMOTE_REMOVED').touch()
    r.state('FINISH boxE archive checksum verified before scratch removal; all own worker trees stopped')
    while time.time() < r.END + 540:
        time.sleep(min(30,r.END+540-time.time()))
    report()


if __name__ == '__main__':
    main()
