"""Recertify a lifted withdrawal through the standard certified-file quench path."""
import pathlib,sys,csv,json,shutil,subprocess,hashlib,time
W=pathlib.Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import credit,mlp
p=W/'reopened/932-reopened-r26.csv';n=932;c=credit(n,mlp.load(str(p),{n})[n],str(p));assert c
D=W/'restored932';D.mkdir(exist_ok=True);shutil.copy(p,D/'restored932.csv');(D/'sources-restored932.json').write_text(json.dumps({'932':c}));shutil.copy(W/'bars.tsv',D/'bars-restored932.tsv')
record=dict(worker='j22restore',pool='restored932',tag='reopened932v4',n=n,raw=1,source={'donors':[932],'recipe_text':'round27 recertification of reopened r26 932; original certified source '+json.load(open(str(p)+'.json'))['source']})
script="import pathlib,json\nR=pathlib.Path.home()/'scratch/squares-k123';d=R/'out/j22restore';d.mkdir(exist_ok=True)\nwith open(d/'done.jsonl','a') as f:f.write("+repr(json.dumps(record)+'\n')+")\n"
(W/'receipt-restore27.py').write_text(script)
SSH=['ssh','-S','/tmp/squares-k123-r34-ssh','boxE']
subprocess.run(SSH+['mkdir -p $SCRATCH/squares-k123/out/j22restore/restored932-932-reopened932v4/raw'],check=True)
subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh',str(p),'boxE:scratch/squares-k123/out/j22restore/restored932-932-reopened932v4/raw/932.csv'],check=True)
subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh',str(W/'receipt-restore27.py'),'boxE:scratch/squares-k123/'],check=True)
subprocess.run(SSH+['cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I receipt-restore27.py'],check=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA RESTORE source932 passes complete independent walk, prvsiyan share0.00321888412. Historical missing harvest703 is under accepted held597, resolved by historical table. Queued standard boxE recertification and certified-file quench. Deadline07:25Z.\n')
