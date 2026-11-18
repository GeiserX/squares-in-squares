"""r30 idle filler: near and take csv of the frozen r29 dirs of other lanes whose side is within 1e-6 above bar30
(or up to 3e-9 below) and whose sha256 the r27-r29 LP index never held. Writes work/lp-extra.txt (gap order)."""
import json,csv,hashlib,math,glob
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');W=S/'take-border-r32/work'
seen=set()
for r in ('r27','r28','r29'):
    p=S/f'take-border-{r}/work/lp/index.json'
    if p.exists(): seen|={v['sha256'] for v in json.load(open(p)).values()}
L={int(r['n']):(float(r['bar'])+1)*math.sqrt(int(r['n'])) for r in csv.DictReader(open(S/'round32-briefs/bar32.tsv'),delimiter='\t')}
out=[]
for f in glob.glob(str(S/'take-*-r29/near/*.csv'))+glob.glob(str(S/'take-*-r29/[0-9]*.csv')):
    if '/take-border-r29/' in f: continue
    try:
        b=Path(f).read_bytes()
        if len(b)>1500000: continue
        h=hashlib.sha256(b).hexdigest()
        if h in seen: continue
        rows=list(csv.DictReader(open(f)));n=int(rows[0]['n'])
        if len(rows)!=n: continue
        xs=[(float(r['x']),float(r['y']),.5*(abs(math.cos(float(r['angle'])))+abs(math.sin(float(r['angle']))))) for r in rows]
        s=max(max(x+q for x,y,q in xs)-min(x-q for x,y,q in xs),max(y+q for x,y,q in xs)-min(y-q for x,y,q in xs))
    except Exception: continue
    g=s-L[n]
    if -3e-9<g<1e-6: out.append((g,n,f))
out.sort()
(W/'lp-extra.txt').write_text('\n'.join(f for g,n,f in out)+'\n')
for g,n,f in out: print(f'{g:.3e}\t{n}\t{f}')
print(len(out),'extra inputs')
