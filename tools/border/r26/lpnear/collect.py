"""Pull the boxC LP batch outputs and floatsafe each one against the live bar (border r26, light)."""
import csv,json,math,glob,os,sys,subprocess
from pathlib import Path
W=Path(__file__).resolve().parent.parent;D=W/'lpnear'
sys.path.insert(0,'.')
import floatsafe
subprocess.run(['rsync','-a','boxC:scratch/squares-border-r26/lp/nout/',str(D/'out')+'/'],check=True)
subprocess.run(['rsync','-a','boxC:scratch/squares-border-r26/lp/run.log',str(D/'run.log')],check=True)
L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
batch={r[0]:r for r in csv.reader(open(D/'batch.tsv'),delimiter='\t')}
for p in sorted(glob.glob(str(D/'out/*/raw/*.csv'))):
 b=p.split('/')[-3];n=int(b.split('_')[1])
 rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
 _,fr,sc,e=floatsafe.work((n,rows))
 if fr is None:print(b,'no cert',e);continue
 side=(sc+1)*math.sqrt(n);bar=L[n]/math.sqrt(n)-1
 print(b,'cert side',repr(side),'bar side',repr(L[n]),'score gap',sc-bar,'COUNTS' if sc<bar-1e-10 else '', batch[b.split('_')[0]][3])
