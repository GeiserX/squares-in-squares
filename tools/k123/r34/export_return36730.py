from pathlib import Path
import sys,json,csv,subprocess,hashlib,shutil,time
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W),str(W/'lane')]
from compact_source28 import credits
from bind_row30 import bind
from publication_source26 import check
records=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()];r=next(r for r in records if r['pool']=='freshreturn29530h8262a038' and r['worker']=='j22c' and r['n']==367);key=r['worker']+'-'+r['pool']+'-'+r['tag'];D=W/'return36730';D.mkdir(exist_ok=True);raw=D/'367.csv'
remote=f'out/{r["worker"]}/{r["pool"]}-367-{r["tag"]}/turn/367-self-+0.000-1.001.csv';subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh','boxE:scratch/squares-k123/'+remote,str(raw)],check=True)
meta=json.load((W/r['pool']/('sources-'+r['pool']+'.json')).open());parents=[meta[str(n)] for n in [295,367]];source=f'k123_join.py {r["tag"]}; changed295/frozen367 return, k123_turn.py self loosen1.001 and fq; numeric_job {key}; immutable input pool {W/r["pool"]/(r["pool"]+".csv")}; pinned donor ancestry: '+credits(parents);row={'n':'367','source':source,'licence':'own return join; '+' | '.join(c['licence'] for c in parents)};row=bind(row,meta,[295,367],r['pool'],key+'-donor');result=check(raw,row);assert result['clean'],result
sha=hashlib.sha256(raw.read_bytes()).hexdigest();out=T/'near'/f'367-threeway28-{sha[:16]}.csv';row.update(numeric_job=key,numeric_csv_sha256=sha,numeric_finish='loosen1.001')
if not out.exists():shutil.copy(raw,out);Path(str(out)+'.json').write_text(json.dumps(row))
(W/'return36730.json').write_text(json.dumps({'path':str(out),'sha256':sha,'side':r['side'],'margin':r['side']-r['bar'],'source_walk_files':result['files']},indent=2));print(out,flush=True)
with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA FINISH licensed return367 donor side{r["side"]}, margin{r["side"]-r["bar"]}; CSVsha256{sha}; {out}; deadline07:25Z.\n')
