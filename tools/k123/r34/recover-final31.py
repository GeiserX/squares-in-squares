"""Recover the mandatory archive after optional metadata timeouts."""
from pathlib import Path
import csv,json,time,subprocess,sys,hashlib,collections,shutil,re,os
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;REPO=Path('$PRIVATE_REPO');LANE=REPO/'lanes/squares';PY=str(S/'venv/bin/python');SSH=['ssh','-S','/tmp/squares-k123-r34-ssh','boxE'];csv.field_size_limit(1<<28)
def log(s):
 line=time.strftime('%FT%TZ',time.gmtime())+' boxA RECOVERY '+s
 print(line,flush=True)
 with (T/'STATE.txt').open('a') as f:f.write(line+'\n')
def run(args,timeout=240,check=True,cwd=None):
 log('RUN '+str(args[:3]));r=subprocess.run(args,cwd=cwd or W,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout);print(r.stdout+r.stderr,flush=True)
 if check and r.returncode:raise RuntimeError(str(args[:3])+' failed')
 return r
def report(complete=False,blocked='archive recovery in progress'):
 rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));base={int(r['n']):float(r['bar']) for r in csv.DictReader((S/'round34-briefs/bar34.tsv').open(),delimiter='\t')};other={}
 for p in S.glob('take-*-r31/take.tsv'):
  if p.parent==T:continue
  for r in csv.DictReader(p.open(),delimiter='\t'):
   try:n=int(r['n']);other[n]=min(other.get(n,base[n]),float(r['new']))
   except (KeyError,ValueError):pass
 records=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()];low=[int(r['n']) for r in rows if float(r['new'])<other.get(int(r['n']),base[int(r['n'])])-1e-10]
 gain=sum(base[int(r['n'])]-float(r['new']) for r in rows);beyond=sum(other.get(int(r['n']),base[int(r['n'])])-float(r['new']) for r in rows if other.get(int(r['n']),base[int(r['n'])])-float(r['new'])>1e-10)
 notes=[f'{len(records)} numerical join and held-probe attempts on {len(set(r["n"] for r in records))} counts. All workers stopped at the common cutoff.','All three retained CSV hashes match the independent full source, certificate-binding and floatsafe checks at00:12UTC.','Final collection and the optional history refresh timed out. The previous index, raw records and immutable manifests are retained. Recovery finishes the mandatory archive and cleanup.']+json.load((W/'measurements28.json').open())
 if (W/'copy-verified25.json').exists():
  v=json.load((W/'copy-verified25.json').open());notes.append(f'Archive verified: {v["files"]} files, {v["bytes"]} bytes, {len(v["checksum_differences"])} checksum differences.')
 nexts=json.load((W/'next28.json').open());nexts.insert(0,'Rebuild round31 completed-geometry keys from the retained records and pinned manifests before resuming a queue. The final history refresh timed out; do not replay those finished starts.')
 r=dict(lane='k123',improved_n=len(low),gain=dict(against_base_bar=gain,beyond_other_live_r31=beyond),take_dir=str(T),summary=f'Certified source layouts: {len(rows)}. Lowest live rows: {len(low)}. '+('Workers stopped, archive verified and boxE scratch removed. Report finalized late after metadata timeout recovery.' if complete else 'Retained CSVs validated; mandatory archive recovery is in progress.'),what_was_measured=notes,next=nexts,commits=json.load((W/'commits26.json').open()),processes_left=0 if complete else 'numerical workers stopped; finalizer active',blocked=blocked,repo=str(REPO)+' (private repo)',branch='main',worktree=str(REPO),pr='')
 (W/'recovery-report31.json').write_text(json.dumps(r,indent=2)+'\n')
 if time.time()>=float((W/'deadline').read_text())+600:
  (T/'report.json.tmp').write_text(json.dumps(r,indent=2)+'\n');(T/'report.json.tmp').replace(T/'report.json')
 return r,rows,records,low,other
def main():
 log('START; no search or quench is restarted')
 for v in json.load((W/'validation25.json').open()):assert v['source_clean'] and v['floatsafe'] and hashlib.sha256((T/(str(v['n'])+'.csv')).read_bytes()).hexdigest()==v['csv_sha256']
 report();(W/'take-final26.json').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'validation':'unchanged CSV hashes from independent00:12 checks'}))
 run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I manifest25.py'],timeout=180)
 archive=W/'boxE-final';archive.mkdir(exist_ok=True)
 with (W/'recovery-tar31.stderr').open('ab') as err:
  sender=subprocess.Popen(SSH+['cd $SCRATCH/squares-k123 && COPYFILE_DISABLE=1 tar -czf - .'],stdout=subprocess.PIPE,stderr=err,start_new_session=True)
  receiver=subprocess.Popen(['tar','-xzf','-','-C',str(archive)],stdin=sender.stdout,stderr=err,start_new_session=True);sender.stdout.close();receiver.wait(timeout=420);sender.wait(timeout=60);assert sender.returncode==0 and receiver.returncode==0
 log('archive stream copied');run([PY,str(W/'verify_archive25.py')],timeout=240);v=json.load((W/'copy-verified25.json').open());assert not v['checksum_differences']
 run(SSH+['test -d $SCRATCH/squares-base && rm -rf -- $SCRATCH/squares-k123'],timeout=90);log('scratch removed after checksum verification; shared base preserved')
 if (W/'finalize26.error').exists():(W/'finalize26.error').replace(W/'finalize26.error.recovered')
 r,rows,records,low,other=report(True,'none');counts=collections.Counter(q['n'] for q in records)
 table=LANE/'results/k123-r31-2026-11-16.tsv'
 with table.open('w') as f:
  wr=csv.writer(f,delimiter='\t');wr.writerow(['kind','n','trials','side','gain_base','gain_other','source','licence','note'])
  for q in rows:
   n=int(q['n']);wr.writerow(['certified',n,counts[n],(float(q['new'])+1)*n**.5,float(q['held'])-float(q['new']),(other.get(n,float(q['held']))-float(q['new']) if other.get(n,float(q['held']))-float(q['new'])>1e-10 else 0),q['source'],q['licence'],'lowest live' if n in low else 'lower follower source'])
  for n in sorted(counts):
   ss=[q['side'] for q in records if q['n']==n and 'side'in q];wr.writerow(['attempts',n,counts[n],min(ss) if ss else '',0,0,'pinned pools in take-k123-r31/work','per-input manifests','raw measured side'])
 section=(W/'round31-section.md').read_text();section=re.sub(r'The four boxE slots ran \d+ numerical attempts on \d+ counts\.',f'The four boxE slots ran {len(records)} numerical attempts on {len(counts)} counts.',section)
 section+='\nFinal collection and history refresh timed out. Their prior index and raw records remain available.\nRecovery verified boxE archive before removing the lane scratch directory.\nThe final CSV hashes match the independent source and clearance checks.\n'
 (W/'round31-section.md').write_text(section);run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round31-section.md')],timeout=30)
 doc=LANE/'avenues/k123.md';old=doc.read_text();at=old.find('\n## Round 31\n');doc.write_text((old[:at] if at>=0 else old).rstrip()+'\n\n'+section)
 dest=LANE/'tools/k123/r31';dest.mkdir(exist_ok=True)
 for p in W.glob('*.py'):shutil.copy(p,dest/p.name)
 paths=['lanes/squares/avenues/k123.md','lanes/squares/results/k123-r31-2026-11-16.tsv','lanes/squares/tools/k123/r31'];assert run(['git','branch','--show-current'],cwd=REPO).stdout.strip()=='main'
 for attempt in range(2):
  run(['git','add','--',*paths],cwd=REPO);c=run(['git','commit','--only','-m','Finalize round31 k123 recovered archive and measurements','--',*paths],cwd=REPO,check=False)
  if c.returncode and 'index.lock'in c.stdout+c.stderr and attempt==0:time.sleep(3);continue
  assert c.returncode==0;break
 sha=run(['git','rev-parse','HEAD'],cwd=REPO).stdout.strip();run(['git','show','--stat',sha],cwd=REPO);files=run(['git','show','--pretty=','--name-only',sha],cwd=REPO).stdout.splitlines();assert all(p in paths[:2] or p.startswith(paths[2]+'/') for p in files)
 pushed=False
 for attempt in range(2):
  pull=run(['git','pull','--rebase','--autostash','origin','main'],cwd=REPO,check=False,timeout=120)
  if pull.returncode and 'CONFLICT'in pull.stdout+pull.stderr:break
  push=run(['git','push','origin','HEAD:main'],cwd=REPO,check=False,timeout=120)
  if not push.returncode:pushed=True;break
 actual=run(['git','log','-1','--format=%H','--grep=^Finalize round31 k123 recovered archive and measurements$'],cwd=REPO).stdout.strip() or sha
 p=W/'commits26.json';commits=json.load(p.open());commits.append(actual);p.write_text(json.dumps(commits));run(SSH+['-O','exit','boxE'],timeout=30,check=False)
 report(True,'none' if pushed else 'Final commit not pushed');(W/'finalize26.done').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime()),'pushed':pushed,'recovered':True}));log('DONE')
if __name__=='__main__':
 try:main()
 except BaseException as e:log('ERROR '+repr(e));(W/'recover-final31.error').write_text(repr(e));report(False,'recovery incomplete: '+repr(e));raise
