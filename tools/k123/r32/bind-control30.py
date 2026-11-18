from pathlib import Path
import json,sys,csv,copy,shutil,hashlib
W=Path(__file__).resolve().parent;O=W.parent.parent/'take-k123-r29/work';sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from bind_row30 import bind
from publication_source26 import check
key='j22c-fresh10401-804-985-j9-10-s0';state=json.load((O/'collect-state.json').open())[key];row=next(csv.DictReader((O/'certs'/key/'out/take.tsv').open(),delimiter='\t'));row['licence']=state['licence'];meta=json.load((O/state['pool']/('sources-'+state['pool']+'.json')).open())
# The archived pool keeps its own immutable location. This control binds only its producer edges.
D=W/'binding-control30';D.mkdir(exist_ok=True);p=D/'985.csv';shutil.copy(O/'certs'/key/'out/985.csv',p);before=hashlib.sha256(p.read_bytes()).hexdigest()
result=bind(row,meta,state['donors'],'control30-no-pool','control985');walk=check(p,result);assert walk['clean'],walk
bad=copy.deepcopy(meta);changed=next(n for n in state['donors'] if bad[str(n)].get('input_file_snapshot'));bad[str(changed)]['input_file_sha256']='0'*64
try:bind(row,bad,state['donors'],'control30-no-pool','bad-hash-control985')
except AssertionError:rejected=True
else:rejected=False
assert rejected and hashlib.sha256(p.read_bytes()).hexdigest()==before
out={'exact985_source_clean':walk['clean'],'files':walk['files'],'bad_packing_hash_rejected':rejected,'certificate_bytes_unchanged':True};(W/'bind-controls30.json').write_text(json.dumps(out,indent=2));print(json.dumps(out),flush=True)
