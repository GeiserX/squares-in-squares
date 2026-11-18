"""Snapshot the explicitly reopened held roots and the source-audited round23a layouts."""
import pathlib,csv,json,hashlib,time,sys
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent;R=pathlib.Path('.');sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp
D=W/'reopened';D.mkdir(exist_ok=True);made=[]
rows={int(r['n']):r for r in csv.DictReader(open(R/'results/forensics-round23a-sources-r24-2026-11-13.tsv'),delimiter='\t')}
for filename,roundn,ns in [('round21-2026-11-13a.csv',21,[415,501,503,921]),('round23-2026-11-13a.csv',23,[228,365,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990])]:
 src=S/'gather'/filename;sha=hashlib.sha256(src.read_bytes()).hexdigest();P=mlp.load(str(src),set(ns))
 for n,A in P.items():
  if roundn==23 and n not in rows:continue
  p=D/f'{n}-reopened-held{roundn}.csv'
  with open(p,'w') as f:
   wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle']);wr.writerows((n,i,*a) for i,a in enumerate(A))
  source=f'held n = {n} of round 21' if roundn==21 else rows[n]['source']
  terms='terms in historical held source record; own discovered Samanyu-matching layouts allowed in round27' if roundn==21 else rows[n]['licence']+' | independently discovered layouts; round27 Samanyu override'
  record=dict(n=n,source=source,licence=terms,packing_file=str(src),packing_file_sha256=sha,source_table=str(R/'results/forensics-round23a-sources-r24-2026-11-13.tsv') if roundn==23 else 'results/round21-best-2026-11-13.tsv')
  pathlib.Path(str(p)+'.json').write_text(json.dumps(record));made.append(str(p))
marker=W/'reopened-inputs27.txt';old=marker.read_text().splitlines();marker.write_text('\n'.join(dict.fromkeys(made+old))+'\n')
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA REOPEN explicit held415/501/503/921 and source-audited round23a roots, {len(made)} per-n byte snapshots, parent packing SHA256 in each sidecar. These roots were not all present as live r26 take files. Front of fresh queue; source checks and geometry dedupe still apply. Deadline05:45Z.\n')
print('root snapshots',len(made),flush=True)
