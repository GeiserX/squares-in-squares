from pathlib import Path
import sys,json,shutil
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];sys.dont_write_bytecode=True
import walker30
D=W/'legacy-diag-control32';D.mkdir(exist_ok=True);public='$SCRATCH/bounties-squares/take-harvest-r32/work/public16/data/gh/kenaznia-doga__s292-upper-bound/n-292-candidate.yaml.csv'
for kind in ['diagnostic','actual']:
 p=D/(kind+'.csv');shutil.copy(W.parent/'488.csv',p);source='own mathematical construction; [deep25 walk: no record '+public+']'
 if kind=='actual':source+='; actual source '+public
 Path(str(p)+'.json').write_text(json.dumps({'n':488,'source':source,'licence':'own'}));texts,missing,seen,helds,refused=walker30.walk(str(p),488)
 assert (public in seen)==(kind=='actual'),(kind,public in seen)
 assert any('[deep25 walk' in t for _,t in texts),'original diagnostic text lost from audit'
r={'diagnostic_path_is_not_input':True,'actual_path_is_walked':True,'original_text_remains_audited':True};(W/'legacy-diag-control32.json').write_text(json.dumps(r));print(json.dumps(r),flush=True)
