"""Final prune of take-twoshort-r32 before the assembler copies.

A row leaves take.tsv when another live r32 take holds the same n at or below it.
Its csv stays in place (a copy also goes to near/): other lanes' rows name our take csv
paths, and a moved file fails the assembler walk of those rows (round 29 trap, round 31 811).

  final31.py --dry                 report only
  final31.py --dry --inject N=S    positive control: pretend another take holds n=N at score S
  final31.py                       prune for real (rename of take.tsv)
"""
import csv, shutil, sys
from pathlib import Path
csv.field_size_limit(10**9)
B=Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r32'
dry='--dry' in sys.argv
inj={int(a.split('=')[0]):float(a.split('=')[1]) for a in sys.argv[sys.argv.index('--inject')+1:] if '=' in a} if '--inject' in sys.argv else {}
lv={}
for p in B.glob('take-*-r32/take.tsv'):
 if p.parent==T:continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:n=int(r['n']);s=float(r['new'])
  except (KeyError,ValueError,TypeError):continue
  if s<lv.get(n,(9,''))[0]:lv[n]=(s,p.parent.name)
for n,s in inj.items():lv[n]=(s,'injected')
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));keep=[];drop=[]
for r in rows:
 n=int(r['n']);o=lv.get(n,(9,''))
 (drop if o[0]<=float(r['new']) else keep).append(r)
 if o[0]<=float(r['new']):print('DROP n=%d: %s %.13f at or below ours %s'%(n,o[1],o[0],r['new']))
print('rows %d keep %d drop %d%s'%(len(rows),len(keep),len(drop),' (dry)' if dry else ''))
if dry or not drop:sys.exit(0)
(T/'near').mkdir(exist_ok=True)
for r in drop:shutil.copy2(T/('%s.csv'%r['n']),T/'near'/('%s-overtaken-twoshort32.csv'%r['n']))
with open(T/'take.tsv.tmp','w',newline='') as f:
 cw=csv.DictWriter(f,fieldnames=list(rows[0].keys()),delimiter='\t');cw.writeheader();cw.writerows(keep)
(T/'take.tsv.tmp').replace(T/'take.tsv')
