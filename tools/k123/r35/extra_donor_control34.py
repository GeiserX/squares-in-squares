from pathlib import Path
import sys,json,subprocess,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp
live={int(f[0]):float(f[1]) for l in (W/'bars.tsv').read_text().splitlines() if (f:=l.split('\t'))};r=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()]
choices=[x for x in r if x.get('code')==0 and not x.get('raw') and x['worker'] in ['j22e','j22f','j22g','j22h','j22i','j22j','j22k'] and 2e-6<x.get('side',1e9)-live.get(x['n'],x['bar'])<.02]
x=min(choices,key=lambda x:x['n']);n=x['n'];key=f'{x["pool"]}-{n}-{x["tag"]}';raw=W/'extra-donor-control34.csv';remote=f'out/{x["worker"]}/{key}/turn/{n}-self-+0.000-{x.get("loosen",1.001):.3f}.csv'
subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r35-ssh','boxE:scratch/squares-k123/'+remote,str(raw)],check=True,timeout=30)
A=mlp.load(str(raw),{n})[n]
def accepts(B,nn,side):return len(B)==nn and abs(mlp.side(B)-side)<3e-8 and mlp.min_gap(B)>-1e-8
assert accepts(A,n,x['side']);assert not accepts(A,n+1,x['side']);assert not accepts(A,n,x['side']+1e-5)
result={'worker':x['worker'],'n':n,'readable':True,'side':float(mlp.side(A)),'record_side':x['side'],'gap':float(mlp.min_gap(A)),'changed_count_rejected':True,'changed_side_rejected':True}
(W/'extra-donor-control34.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH extra-box donor control: '+json.dumps(result)+'; work/extra-donor-control34.json, deadline16:25Z.\n')
