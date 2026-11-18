"""Commit a reviewable checkpoint while numerical workers continue."""
from pathlib import Path
import sys,json,re,shlex,time
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));import finish26 as f
(W/'owned-helpers26.json').write_text(json.dumps([p.name for p in W.glob('*.py')]))
f.artifacts()
doc=f.LANE/'avenues/k123.md';text=doc.read_text();text=text.replace('## Round 30\n\n','## Round 30\n\nCheckpoint at 15:00 UTC. Search continues through 17:45 UTC.\n\n');doc.write_text(text)
paths=['lanes/squares/avenues/k123.md','lanes/squares/results/k123-r30-2026-11-15.tsv','lanes/squares/tools/k123/r30'];msg='Checkpoint round 30 k123 search and source bindings'
assert f.git(['branch','--show-current']).stdout.strip()=='main'
cmd=shlex.join(['git','add','--',*paths])+' && '+shlex.join(['git','commit','--only','-m',msg,'--',*paths]);r=f.run(['/bin/zsh','-c',cmd],cwd=f.REPO,check=False)
if r.returncode and 'index.lock' in r.stdout+r.stderr:
 time.sleep(3);r=f.run(['/bin/zsh','-c',cmd],cwd=f.REPO,check=False)
assert r.returncode==0,r.stdout+r.stderr
m=re.search(r'^\[[^\]]+ ([0-9a-f]{7,40})\]',r.stdout,re.M);assert m
sha=f.git(['rev-parse',m[1]]).stdout.strip();f.git(['show','--stat',sha]);files=f.git(['show','--pretty=','--name-only',sha]).stdout.splitlines();assert all(p in paths[:2] or p.startswith(paths[2]+'/') for p in files)
pushed=False
for attempt in range(2):
 r=f.git(['pull','--rebase','--autostash','origin','main'],check=False)
 if r.returncode and 'CONFLICT' in r.stdout+r.stderr:break
 r=f.git(['push','origin','HEAD:main'],check=False)
 if not r.returncode:pushed=True;break
 time.sleep(3)
actual=f.git(['log','-1','--format=%H','--grep=^'+msg+'$']).stdout.strip() or sha
p=W/'commits26.json';commits=json.load(p.open()) if p.exists() else [];commits.append(actual);p.write_text(json.dumps(commits));f.journal('FINISH checkpoint commit '+actual+(' pushed to origin/main' if pushed else ' not pushed')+'; four boxE numerical slots continue until17:45Z')
