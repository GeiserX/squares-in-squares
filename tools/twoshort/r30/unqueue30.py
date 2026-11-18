# Round 29: drop pending jobs and legs whose intake input was withdrawn by its lane (sha256 in a WITHDRAW handoff line).
# A running kick of a withdrawn input is killed; its worker records the stop and moves on.
import json,re,pathlib,subprocess,sys,time
W=pathlib.Path('$SCRATCH/bounties-squares/take-twoshort-r30/work');B=W.parent.parent
wd=set()
for l in (B/'handoff-r30.log').read_text().splitlines():
 if 'WITHDRAW' in l:wd.update(re.findall(r'sha256 ([0-9a-f]{64})',l))
def tag_of(name):
 m=re.match(r'\d{3}-(?:\d\d-)?(?:leg-)?(.+)-\d{4}\.json$',name);return m and m[1]
bad={}
for f in W.glob('intake/*.json'):
 if f.name.endswith('-ancestry.json'):continue
 try:d=json.load(open(f))
 except ValueError:continue
 if d.get('sha256') in wd:bad[f.stem]=d['origin']
r=subprocess.run(['ssh','boxE','cd $SCRATCH/squares-twoshort; ls jobs; echo ---; ls locks; echo ---; ls done; echo ---; ps -axo pid,command | grep -E "lane/(invent_rest|midm_scan|zone_corner)" | grep squares-twoshort | grep -v grep'],capture_output=True,text=True).stdout.split('---\n')
jobs,locks,done,ps=[x.split('\n') for x in r]
locks=set(locks);done=set(x.removesuffix('.done') for x in done)
drop=[j for j in jobs if j.endswith('.json') and j not in locks and tag_of(j) in bad]
kill=[]
for line in ps:
 m=re.match(r'\s*(\d+) ',line)
 if not m:continue
 for t in bad:
  if '/runs/'+t+'-s' in line or ' '+t+' ' in line or 'starts/'+t+'.csv' in line or 'runs/'+t+'-' in line:kill.append((m[1],t))
cmd=''.join('mkdir -p locks/%s; rm -f jobs/%s;'%(j,j) for j in drop)
if kill:cmd+='kill '+' '.join(k for k,_ in kill)+';'
if cmd and '--dry' not in sys.argv:subprocess.run(['ssh','boxE','cd $SCRATCH/squares-twoshort; '+cmd])
for j in drop:
 lj=W/'jobs'/j
 if lj.exists() and '--dry' not in sys.argv:(W/'withdrawn').mkdir(exist_ok=True);lj.rename(W/'withdrawn'/j)
stamp=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
msg='%s QUEUE unqueue30: %d withdrawn intake tags; dropped %d pending jobs/legs; killed %d running kicks %s'%(stamp,len(bad),len(drop),len(kill),' '.join(t for _,t in kill))
print(msg);print(' '.join(drop))
if (drop or kill) and '--dry' not in sys.argv:open(W.parent/'STATE.txt','a').write(msg+'\n')
