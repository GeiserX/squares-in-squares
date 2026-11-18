"""Round 33 twoshort screen d (deep queue, second pass): held rows that changed in round 32 (border info changed32) whose
unprobed 900 s kick lines of rounds 31 and 32 came before the row's last round 32 certified line, so their current geometry
has had no unprobed 900 s kick. A line counts as unprobed unless it names a probe (120 s probe, probe 330 s, probe120,
probe N s with N > 0). Lines of round 33 count from the start of the round. Rows with no round 32 certified line are left out
(their change time is unknown). Largest board gap first."""
import json,re,sys,csv
from pathlib import Path
B=Path('$SCRATCH/bounties-squares')
info={int(k):v for k,v in json.load(open(B/'take-border-r33/work/held33/info.json')).items()}
src={int(r['n']):r['source'] for r in csv.DictReader(open(B/'round33-briefs/bar33.tsv'),delimiter='\t')}
CLOSED={692,746,643,341,926,863,695,686,859,989,812,416,634,912,588}
def probed(l):
  m=re.search(r'probe\s*(\d+)|(\d+)\s*s probe|probe (\d+) s',l)
  if m: return int(next(x for x in m.groups() if x))>0
  return False
cert={}
for line in open(B/'handoff-r32.log',errors='replace'):
  m=re.match(r'(\S{19})\S* (\S+) -> .*certified n=(\d+)',line,re.I)
  if m: cert[int(m[3])]=m[1]
lines=[(lg,l) for lg in ('handoff-r32.log','handoff-r33.log') for l in open(B/lg,errors='replace') if re.search(r'\b900\s*s|900s',l) and re.search(r'kick|claim',l,re.I)]
ok=[]
for n,v in sorted(info.items(),key=lambda x:-(x[1]['gap'] or 0)):
  if not v['gap'] or v['gap']<=1e-9 or not v['changed32'] or n not in cert: continue
  if v['rigid'] or v['bad'] or v['lattice'] or v['spent'] or n in CLOSED: continue
  if not src.get(n,'').startswith('held round32'): continue
  after=[l for lg,l in lines if re.search(r'\bn\s*=\s*%d\b'%n,l) and not probed(l) and (lg.endswith('33.log') or l[:19]>cert[n])]
  if after: continue
  ok.append(dict(n=n,gap=v['gap'],cert32=cert[n]))
json.dump(dict(ok=ok),open(sys.argv[1],'w'),indent=1)
print(len(ok),[(o['n'],'%.1e'%o['gap']) for o in ok])
