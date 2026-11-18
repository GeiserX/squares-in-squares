"""Round 26 initial queue for the border lane.
Adopts from the frozen take-border-r25 queue (read only; files are copied into this round's q/):
 1. saved chains that stopped within SAVED_GAP of the r26 bar, with their record and best packing, so they go on;
 2. clean unstarted starts, ranked by the expected end: margin now minus the best give-back measured on the same
    (donor, n) pair in rounds 24 and 25 (0.3 of the margin when the pair has no record).
Measured dead ends are skipped: a pair with 3 or more records whose best end is more than DEAD_GAP above the r26 bar.
Every adopted start passes audit_manifest and the r26 source policy (bare 29e12ff3 names and the other exclusions of
the r26 brief refuse it)."""
from pathlib import Path
import csv,json,math,shutil,hashlib,re,collections
S=Path('$SCRATCH/bounties-squares')
OLD=[S/'take-border-r24/work',S/'take-border-r25/work']
SAVED_GAP=1e-3;DEAD_GAP=1.5e-3;MAX_EXPECTED=4e-3
csv.field_size_limit(1<<26)
def records(L):
 pair=collections.defaultdict(list)
 for W in OLD:
  man={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')}
  for p in (W/'q').glob('*.k*.json'):
   m=re.match(r'^(.*)\.k(\d+)\.json$',p.name)
   if not m:continue
   r=man.get(m[1])
   if not r:continue
   try:j=json.load(open(p))
   except ValueError:continue
   n=int(r['n']);pair[(int(r['donor']),n)].append(dict(giveback=j['s_start']-j['s_final'],end=j['s_final']-L[n],ident=m[1],k=int(m[2]),W=W,j=j,r=r))
 return pair
def initialize(g,ready=False):
 if not ready:return
 W=g['W'];L=g['L'];log=g['log'];sp=g['sp']
 if (W/'initialized').exists():return
 pair=records(L)
 src=OLD[-1];man={r['id']:r for r in csv.DictReader(open(src/'q/manifest.tsv'),delimiter='\t')}
 adopted=[];saved=0;dead=collections.Counter();unclean=collections.Counter();far=0
 for ident,r in man.items():
  st=src/'q'/(ident+'.start.txt')
  if not st.exists():continue
  n=int(r['n']);d=int(r['donor']);rec=src/'q'/(ident+'.k0.json')
  recs=pair.get((d,n),[])
  if len(recs)>=3 and min(x['end'] for x in recs)>DEAD_GAP:dead[(d,n)]+=1;continue
  margin=float(r['built_L'])-L[n]
  if rec.exists():
   j=json.load(open(rec))
   if not(j.get('cut') and j['round']<6 and j['s_final']-L[n]<SAVED_GAP):continue
   expected=j['s_final']-L[n];prio=-130
  else:
   gb=max([x['giveback'] for x in recs],default=.3*max(margin,0))
   expected=margin-gb;prio=10+100*expected
   if expected>MAX_EXPECTED:far+=1;continue
  if not g['audit_manifest'](r):unclean[(d,n,'audit')]+=1;continue
  pol=sp.manifest_policy(r)
  if pol['status']!='none':unclean[(d,n,pol.get('reason','')[:40])]+=1;continue
  md=hashlib.md5(st.read_bytes()).hexdigest()
  if md in g['queued']:continue
  shutil.copyfile(st,W/'q'/st.name)
  if r.get('donor_copy') and (src/'q'/r['donor_copy']).exists():shutil.copyfile(src/'q'/r['donor_copy'],W/'q'/r['donor_copy'])
  if rec.exists():
   shutil.copyfile(rec,W/'q'/rec.name);shutil.copyfile(src/'q'/j['best'],W/'q'/j['best']);saved+=1
  (W/'q'/(ident+'.job.json')).write_text(json.dumps(dict(start=st.name,priority=prio,adopted_r25=True,expected=expected)))
  adopted.append(r);g['queued'].add(md)
 if adopted:
  p=W/'q/manifest.tsv';exists=p.exists()
  cols=open(p).readline().rstrip('\n').split('\t') if exists else list(adopted[0])
  with p.open('a') as f:
   wr=csv.DictWriter(f,fieldnames=cols,delimiter='\t',extrasaction='ignore')
   if not exists:wr.writeheader()
   wr.writerows(adopted)
 log(f'ADOPT {len(adopted)} r25 starts ({saved} saved chains within {SAVED_GAP} of the r26 bar). Skipped: measured dead-end pairs {dict(dead)}; expected end above {MAX_EXPECTED}: {far}; unclean {dict(unclean)}')
 (W/'initialized').write_text('initial queue completed')
