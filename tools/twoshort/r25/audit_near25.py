from pathlib import Path
import sys,json,shutil,time
W=Path(__file__).parent;T=W.parent;sys.path.insert(0,str(W));from admit25 import store
bad=[];good=[]
for p in (T/'near').glob('*.csv'):
 q=p.with_suffix('.json')
 if not q.exists():
  dst=W/'excluded-near';dst.mkdir(exist_ok=True);p.replace(dst/p.name);bad.append(dict(file=str(p),errors=['missing source metadata']));continue
 md=json.load(open(q));mods=md.get('modules')
 source=md.get('source','') if not mods else json.dumps(mods)
 lic=md.get('licence','') if not mods else '; '.join(sorted({m['licence'] for m in mods}))
 ok,proof=store(dict(source=source,licence=lic),n=int(p.stem.split('-')[0]))
 if ok:good.append(str(p));continue
 dst=W/'excluded-near';dst.mkdir(exist_ok=True);p.replace(dst/p.name);q.replace(dst/q.name);bad.append(dict(file=str(p),errors=proof['closure']['errors'][:3]))
(W/'near-source-audit.json').write_text(json.dumps(dict(good=good,retired=bad),indent=2));print('near audit',len(good),'good',len(bad),'retired')
if bad:
 with open(T.parent/'handoff-r25.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' twoshort -> all: source audit retired '+str(len(bad))+' untraced near files; do not use these paths, list '+str(W/'near-source-audit.json')+'\n')

import os
sys.stdout.flush();sys.stderr.flush();os._exit(0)
