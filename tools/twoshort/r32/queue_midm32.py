"""Round 32 twoshort, 15:15Z: queue 900 s midm_scan lkick,kick jobs with no probe (border's measured kind: in round 31 its
unprobed 900 s held kicks gave 2 rows in 9 runs, 494 and 864, after a first seed found nothing, while 73 probed kicks gave 0)
on held round 31 b rows with the largest board gap that no other lane names in any claim or kick line of handoff-r32.log.
Our own dry 150 s lkicks of the same rows do not block. One seed (3401) per row. Jobs are named 008-* so they run before
the remaining 010-* lkick seconds; legs while a step moves 1e-6 of side (worker rule), 300 s each.
  queue_midm32.py controls       queue the two no-probe controls (scaled 793 must move, rigid 730 must not)
  queue_midm32.py rows K         claim and queue the K best rows"""
import json,re,sys,subprocess
from pathlib import Path
W=Path(__file__).parent
src=open(W/'manage32.py').read().split("if __name__=='__main__':")[0]
g={'__file__':str(W/'manage32.py')};exec(src,g)
HOST,RD,B=g['HOST'],g['RD'],g['B']
def push(name,j):
  f=W/'jobsent'/name;f.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(f),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
if sys.argv[1]=='controls':
  for tag,start,sha,n,bar,root in [
   ('control-midmnp793','starts/control-scaled793.csv','84da164010f752886d525be122216e9f3488710864d4f51283352955474cf2bb',793,0.0177543703233769,28.660223288412816),
   ('control-midmnprigid730','starts/control-rigid730.csv','fe2ff1d137ccd9eb0c73d405cd1dfedf3617f79288b94be49a7310f35297cd7d',730,0.018591072153904653,27.52081528149735)]:
    j=dict(tag=tag,n=n,start=start,start_sha256=sha,seed=3320,seconds=60,probe=0,tool='midm',leg_seconds=300,legs=8,priority=0,control=True,bar=bar,root_side=root,chain=[start])
    f=W/'t3'/('000-%s-3320.json'%tag);f.write_text(json.dumps(j,indent=1))
    subprocess.run(['rsync','-a',str(f),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  sys.exit()
K=int(sys.argv[2]);lv=g['live']()
other=set()
for line in open(B/'handoff-r32.log',errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort' or not re.search(r'claim|kick',line,re.I):continue
  for x in re.findall(r'\bn ?= ?(\d+)',line):other.add(int(x))
  for x in re.findall(r'(?:held\w*|take-[\w-]+-r\d+)/(\d+)\.csv',line):other.add(int(x))
  for x in re.findall(r'starts/(\d+)-',line):other.add(int(x))
wd=g['withdrawn']()
done={json.load(open(p))['n'] for p in (W/'jobsent').glob('008-*.json')}
sel=json.load(open(W/'sel32.json'));cand=[]
for o in sel['all']:
  n=o['n']
  if n in g['OUT'] or n in lv or n in other or n in done:continue
  if [w for w in o['why'] if not w.startswith('lkick line')] or o['shared']:continue
  s=g['src'].get(n,('','',''))
  if any(b in s[1] for b in g['BADSRC']) and 'own Samanyu' not in s[1]:continue
  cand.append(o)
cand.sort(key=lambda o:-o['gap'])
import csv
for o in cand[:K]:
  n=o['n'];f=W/'starts'/('%d-held31b.csv'%n)
  if not f.exists():
    with open(f,'w',newline='') as gq:
      cw=csv.writer(gq);cw.writerow(['n','square_id','x','y','angle'])
      for r in g['held_rows'](n):cw.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
  h=g['sha'](f)
  if h[:12] in wd:g['state']('SKIP n=%d start bytes %s named by a WITHDRAW line'%(n,h[:12]));continue
  tag='m900-%d-%s'%(n,h[:8]);s=g['src'].get(n,('','',''))
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=3401,seconds=900,probe=0,tool='midm',leg_seconds=300,leg_probe=0,bar=g['bar'][n],root_side=g['L'][n],legs=0,priority=8,chain=[str(f)],held_src=s[0])
  g['handoff']('claim: 900 s midm_scan lkick,kick with no probe (seed 3401, boxE; legs of 300 s while a step moves 1e-6 of side) of n=%d, start bytes sha256 %s, the held round 31 b row (no claim or kick line of another lane names n=%d in r32; board score gap %.2e; border measured 2 rows in 9 unprobed 900 s held kicks in r31), %s'%(n,h,n,o['gap'],f))
  subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  push('008-%s-3401.json'%tag,j)
  g['state']('QUEUE %s n=%d seed 3401 held round 31 b side %.12f gap %.2e; boxE midm_scan lkick,kick 900 s, no probe; log %s/runs/%s-s3401; deadline 16:55Z search, 17:15Z quench'%(tag,n,g['L'][n],o['gap'],RD,tag))
