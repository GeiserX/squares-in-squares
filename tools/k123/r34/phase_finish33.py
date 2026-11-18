"""Quench a source-cleared constructive model and return real crossings to the normal collector."""
from pathlib import Path
import sys,os,csv,json,runpy,math,hashlib,shutil
R=Path.home()/'scratch/squares-k123';sys.path[:0]=[str(R),str(R/'lane')]
import finesafe,methods_lp as mlp
j=json.load(open(sys.argv[1]));D=R/'out/phase33'/j['tag'];D.mkdir(exist_ok=True);p=R/j['input'];rows=list(csv.DictReader(p.open()));n=len(rows);_,fr,sc,e=finesafe.work((n,rows));assert fr is not None
I=D/'certified';I.mkdir(exist_ok=True)
with (I/(str(n)+'.csv')).open('w') as h:
 w=csv.DictWriter(h,['n','square_id','x','y','angle']);w.writeheader();w.writerows(fr)
sys.argv=['cert_once22.py',str(I),str(D/'fq'),str(Path.home()/'scratch/squares-base/fq'),'unused'];runpy.run_path(str(R/'cert_once22.py'),run_name='__main__')
p=D/'fq'/(str(n)+'-fq-tight.csv');P=mlp.load(str(p),{n})[n];rawside=float(mlp.side(P));rows=list(csv.DictReader(p.open()));_,fr,sc,e=finesafe.work((n,rows));assert fr is not None
base={int(r['n']):float(r['score']) for r in csv.DictReader((R/'details-base25.csv').open())};bars={int(l.split('\t')[0]):float(l.split('\t')[1]) for l in (R/'bars.tsv').read_text().splitlines()};win=sc<base[n]-1e-10
result={'n':n,'input':j['input'],'raw_side_after_fq':rawside,'certified_side':(sc+1)*math.sqrt(n),'bar_side':(base[n]+1)*math.sqrt(n),'score':sc,'gain':base[n]-sc,'below_bar':win,'full_fq_receipt':str(D/'fq'/(str(n)+'-quench.json'))}
if win:
 tag=j['tag'];dest=R/'out/steps'/tag/'raw';dest.mkdir(parents=True,exist_ok=True);shutil.copy(p,dest/(str(n)+'.csv'))
 record={'worker':'steps','pool':'phasepool33','tag':tag,'n':n,'raw':1,'bar':bars[n],'side':rawside,'mechanism':'fixed-phase-free-mask33','source':{'recipe_text':'own fixed-parent-phase optional-mask MILP and continuous mask refit, then border finesafe and full default/polish fq; measured task '+j['tag']+' input '+j['input'],'donors':[261,367]}}
 (R/'out/steps').mkdir(exist_ok=True)
 with (R/'out/steps/done.jsonl').open('a') as h:h.write(json.dumps(record)+'\n')
(D/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
