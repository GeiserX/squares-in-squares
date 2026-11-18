"""Give a third band join a changed, non-winning two-band intermediate."""
import pathlib,json,csv,time,sys,re,subprocess,hashlib,shutil
from pathlib import Path
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(20000000)
if (W/'restart-third29').exists():
 (W/'restart-third29').unlink();__import__('os').execv(sys.executable,[sys.executable,str(W/'background29.py'),'third'])
marker=W/'intermediate-last28'
if marker.exists() and time.time()-marker.stat().st_mtime<120:raise SystemExit
marker.touch();seenfile=W/'intermediate-seen28.json';seen=set(json.load(seenfile.open())) if seenfile.exists() else set()
from provenance24 import mlp,credit
from compact_source28 import credits
from publication_source26 import check
import k123_join as kj
records=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()]
def ident(r):return r['worker']+'-'+r['pool']+'-'+r['tag']
# The known winning756 is a real reader control for imported own join outputs.
control=next((r for r in records if r['n']==756 and r.get('raw')),None)
if control and not (W/'intermediate-control28.json').exists():
 p=T/'756.csv'
 if p.exists():
  A=mlp.load(str(p),{756})[756];X=kj.Lay(756,*kj.norm(A),'756');assert len(A)==756 and len(X.G)>=10
  (W/'intermediate-control28.json').write_text(json.dumps({'n':756,'chains':len(X.G),'side':mlp.side(A),'gap':float(mlp.min_gap(A))}));print('own join reader control756',len(X.G),mlp.side(A),flush=True)
live={int(f[0]):float(f[1]) for line in (W/'bars.tsv').read_text().splitlines() if len(f:=line.split('\t'))>=2}
def margin(r):return r.get('side',1e9)-live.get(r['n'],r['bar'])
choices=[r for r in records if ident(r) not in seen and r.get('code')==0 and not r.get('raw') and 2e-6<margin(r)<.02 and r['worker'] in ['j22a','j22b','j22c','j22d']]
counts={}
for p in (T/'near').glob('*-threeway28-*.csv'):
 nn=int(p.name.split('-')[0]);counts[nn]=counts.get(nn,0)+1
wide_slot=sum(counts.values())%2==1
choices.sort(key=lambda r:((margin(r)<.001) if wide_slot else (margin(r)>=.001),counts.get(r['n'],0),margin(r),-int(''.join(ch for ch in r['pool'] if ch.isdigit()) or '0')))
for r in choices[:3]:
 key=ident(r);seen.add(key);seenfile.write_text(json.dumps(sorted(seen)))
 with (W/'intermediate-attempts29.jsonl').open('a') as h:h.write(json.dumps({'key':key,'record':r,'started':time.time()})+'\n')
 n=r['n'];pool=r['pool'];mp=W/pool/('sources-'+pool+'.json')
 if not mp.exists():continue
 match=re.fullmatch(r'(\d+)(r?)-(\d+)(r?)-j(\d+)-(\d+)-s(-?\d+)',r['tag'])
 if not match:continue
 meta=json.load(mp.open());ns=[match[1],match[3]]
 from source25 import audit
 parents=[audit(meta[z]) for z in ns]
 if not all(parents):continue
 D=W/'intermediates28'/key;D.mkdir(parents=True,exist_ok=True)
 remote=f'out/{r["worker"]}/{pool}-{n}-{r["tag"]}/turn/{n}-self-+0.000-1.001.csv';raw=D/'numeric.csv'
 copy=subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r29-ssh','boxE:scratch/squares-k123/'+remote,str(raw)],capture_output=True,text=True,timeout=30)
 if copy.returncode:continue
 A=mlp.load(str(raw),{n})[n]
 if len(A)!=n:continue
 X=kj.Lay(n,*kj.norm(A),str(n))
 if len(X.G)<10:continue
 digest=hashlib.sha256(raw.read_bytes()).hexdigest();out=T/'near'/f'{n}-threeway28-{digest[:16]}.csv'
 source=f'k123_join.py {r["tag"]}; k123_turn.py self, loosen1.001, fq; non-winning two-band intermediate for a changed third-band join, original side {r["side"]:.14g}, margin {margin(r):.12g}; immutable input pool {W/pool/(pool+".csv")}; pinned donor ancestry: '+credits(parents)
 row=dict(n=str(n),source=source,licence='own join intermediate, terms in the pinned donor ancestry',numeric_job=key,numeric_csv_sha256=digest)
 Path(str(raw)+'.json').write_text(json.dumps(row));checked=check(raw,row)
 if not checked['clean']:continue
 Path(str(out)+'.json.tmp').write_text(json.dumps(row));Path(str(out)+'.json.tmp').replace(Path(str(out)+'.json'));shutil.copy(raw,str(out)+'.tmp');Path(str(out)+'.tmp').replace(out)
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: uncounted three-way join donor n={n}, side={mlp.side(A):.14g}, above bar by{mlp.side(A)-live.get(n,r["bar"]):.6g}; ordinary fq already run, changed third-band joins next, {out}\n'
 with (S/'handoff-r29.log').open('a') as f:f.write(line)
 with (T/'STATE.txt').open('a') as f:f.write(line.rstrip()+f'; source proof{D}/source-walk26.json; deadline11:45Z\n')
 print('three-way intermediate',n,digest,r['side']-r['bar'],flush=True);break
seenfile.write_text(json.dumps(sorted(seen)))
