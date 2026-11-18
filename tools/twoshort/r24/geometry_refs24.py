from pathlib import Path
import json,shutil,hashlib,csv,sys
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');W=B/'take-twoshort-r24/work';O=B/'take-twoshort-r23/work/boxE23';D=W/'reference';D.mkdir(exist_ok=True);refs=[];seen=set()
for p in (O/'jobs').glob('*.json'):
 if not (O/'locks'/p.name).exists():continue
 j=json.load(open(p));st=j.get('start')
 if not st:continue
 q=O/st.split('/scratch/squares-twoshort/')[-1]
 if not q.exists():continue
 digest=hashlib.sha256(q.read_bytes()).hexdigest()
 if digest in seen:continue
 seen.add(digest);name=str(j['n'])+'-'+digest[:16]+'.csv';shutil.copy2(q,D/name);refs.append(dict(n=j['n'],file='reference/'+name,source=str(q)))
(D/'index.json').write_text(json.dumps(refs,indent=2));print('geometry references',len(refs))
p=W/'specs24.py';s=p.read_text().replace("for jp in (R/'jobs').glob('*.json'):","refs=json.load(open(R/'reference/index.json')) if (R/'reference/index.json').exists() else []\n  for old in refs:\n   if old['n']!=n:continue\n   ref=R/old['file'];b,bs=load(ref)\n   if abs(side-bs)<2e-8 and distance(a,side,b)<2e-8:duplicate=str(ref);break\n  if duplicate:\n   done[-1]['duplicate']=duplicate;continue\n  for jp in (R/'jobs').glob('*.json'):");p.write_text(s)
