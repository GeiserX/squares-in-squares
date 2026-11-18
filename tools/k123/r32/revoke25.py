import pathlib,json,subprocess
from provenance24 import W,S
from source25 import audit
bad={};stats={}
for mp in W.glob('*/sources-*.json'):
 j=json.load(open(mp));ns=[]
 for nn,c in j.items():
  if not audit(c):ns.append(int(nn))
 if ns:bad[mp.parent.name]=ns
 stats[mp.parent.name]=[len(j),len(ns)]
p=W/'blocked-inputs.json';p.write_text(json.dumps(bad));print('AUDITED',stats,flush=True)
subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r32-ssh','-q',str(p),'boxE:scratch/squares-k123/blocked-inputs.json'],check=True)
subprocess.run(['ssh','-S','/tmp/squares-k123-r32-ssh','boxE',"cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I - <<'REMOTE'\nimport json,pathlib,re,subprocess,os,signal\np=pathlib.Path('queue.tsv');bad=json.load(open('blocked-inputs.json'));old=p.read_text().splitlines();keep=[]\nfor l in old:\n w=l.split('\\t')\n if len(w)<8:continue\n m=re.match(r'(\\d+)r?-(\\d+)r?-j',w[1])\n if m and set(map(int,m.groups())) & set(bad.get(w[7],[])):continue\n keep.append(l)\np.with_suffix('.revoke.tmp').write_text('\\n'.join(keep)+'\\n');p.with_suffix('.revoke.tmp').replace(p)\nfor l in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines():\n if 'lane/k123_turn.py ' not in l:continue\n m=re.search(r'/out/j22[a-d]/([^/]+)-(\\d+)-(\\d+)r?-(\\d+)r?-j',l)\n if m and set(map(int,m.groups()[2:]))&set(bad.get(m[1],[])):\n  pid=int(l.split()[0])\n  if os.getpgid(pid)==pid:os.killpg(pid,signal.SIGTERM);print('stopped forbidden input job',pid,m[1])\nprint('revoked queue',len(old),'->',len(keep))\nREMOTE"],check=True)
