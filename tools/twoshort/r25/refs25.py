from pathlib import Path
import json,csv,sys,shutil,hashlib
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent;O=B/'take-twoshort-r24/work/boxE24';sys.path.insert(0,str(W));from admit25 import store
rows=[];seen=set()
for p in (O/'done').glob('*.json'):
 j=json.load(open(p));st=j.get('start','')
 if not st or not j.get('tries') or j.get('tag','').startswith('control'):continue
 if not store(dict(source=j['source'],licence=j['licence']))[0]:continue
 q=O/st.split('/scratch/squares-twoshort/')[-1]
 if not q.exists():continue
 digest=hashlib.sha256(q.read_bytes()).hexdigest()
 if digest in seen:continue
 seen.add(digest);name=str(j['n'])+'-'+digest[:16]+'.csv';shutil.copy2(q,W/'reference'/name);rows.append(dict(n=j['n'],file='reference/'+name,source=str(q)))
(W/'reference/index.json').write_text(json.dumps(rows,indent=2));print('clean previous geometry references',len(rows))
