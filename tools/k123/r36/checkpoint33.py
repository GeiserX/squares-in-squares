"""Preserve an early copy and push before the numerical cutoff."""
from pathlib import Path
import subprocess,time,datetime,os,shutil,json,shlex
W=Path(__file__).resolve().parent;T=W.parent;REPO=Path('$PRIVATE_REPO');L=REPO/'lanes/squares';PY=str(T.parent/'venv/bin/python')
def note(s):
 with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA CHECKPOINT33 '+s+'\n')
def run(args,timeout=120,cwd=None):
 r=subprocess.run(args,cwd=cwd or W,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout);print(r.stdout,flush=True);r.check_returncode();return r.stdout
at=datetime.datetime(2026,11,16,23,30,tzinfo=datetime.timezone.utc).timestamp()
while time.time()<at:time.sleep(min(30,at-time.time()))
note('START pre-cutoff archive and exact-path push. Numeric jobs continue within four boxE slots.')
D=W/'boxE-pre33';D.mkdir(exist_ok=True)
try:
 run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r36-ssh','boxE:scratch/squares-k123/',str(D)+'/'],timeout=600)
 run([PY,str(W/'history28.py')],timeout=120)
 run([PY,str(W/'report33.py'),'--artifacts'],timeout=60)
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round33-section.md')])
 p=L/'avenues/k123.md';s=p.read_text().split('\n## Round 33\n')[0];section=(W/'round33-section.md').read_text().replace('At the final comparison','At this comparison').replace('The search and quench cutoff was','The search and quench cutoff is');p.write_text(s.rstrip()+'\n\n'+section)
 dest=L/'tools/k123/r33';dest.mkdir(exist_ok=True)
 for p in W.glob('*.py'):shutil.copy(p,dest/p.name)
 paths=['lanes/squares/avenues/k123.md','lanes/squares/results/k123-r33-2026-11-17.tsv','lanes/squares/tools/k123/r33']
 command=shlex.join(['git','add','--',*paths])+' && '+shlex.join(['git','commit','--only','-m','Checkpoint round 33 k123 measurements','--',*paths])
 try:run(['/bin/zsh','-c',command],cwd=REPO)
 except subprocess.CalledProcessError as e:
  if 'index.lock' not in (e.output or ''):raise
  time.sleep(3);run(['/bin/zsh','-c',command],cwd=REPO)
 sha=run(['git','rev-parse','HEAD'],cwd=REPO).strip();run(['git','show','--stat',sha],cwd=REPO)
 files=run(['git','show','--pretty=','--name-only',sha],cwd=REPO).splitlines();assert all(p in paths[:2] or p.startswith(paths[2]+'/') for p in files)
 cp=W/'commits26.json';commits=json.load(cp.open()) if cp.exists() else [];commits.append(sha);cp.write_text(json.dumps(commits))
 run(['git','pull','--rebase','--autostash','origin','main'],cwd=REPO);run(['git','push','origin','HEAD:main'],cwd=REPO)
 actual=run(['git','log','-1','--format=%H','--grep=^Checkpoint round 33 k123 measurements$'],cwd=REPO).strip()
 if actual:commits[-1]=actual;cp.write_text(json.dumps(commits))
 note('FINISH archive copied, numerical history rebuilt, own paths verified and pushed. Numerical shutdown remains16:05Z; hard cutoff23:45Z.')
except BaseException as e:
 note('ERROR '+repr(e));(W/'checkpoint32.error').write_text(repr(e));raise
