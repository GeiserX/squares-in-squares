from common29 import *
from history29 import trace
for row in rows(T/'take.tsv'):
 n=int(row['n']);sha=hashlib.sha256((T/f'{n}.csv').read_bytes()).hexdigest()
 a=next((read(p,{}) for p in (W/'audited').glob('*.json') if read(p,{}).get('certified_output_sha256')==sha and read(p,{}).get('accepted')),None)
 c=read(a['input_proof'],{});h=trace(c['source'],c['licence'],dict(producer=c.get('metadata',{}),expanded_records=c.get('expanded',{}).get('records',[]),unresolved_csv=c.get('expanded',{}).get('unresolved_csv',[])),n)
 atomic(W/f'retained-rewalk-{n}.json',h);print('REWALK',n,'issues',h.get('issues'),'excluded',h.get('excluded'),'pins',len(h.get('snapshots',[])),flush=True)
 if not h.get('issues') and not h.get('excluded'):
  a['walked']=h;a['resolved_source_snapshots']=h.get('snapshots',[]);atomic(W/'audited'/(a['tag']+'.json'),a);note(f'FINAL_SOURCE_REWALK n{n} clear, {len(h.get("snapshots",[]))} pinned source records, output sha{sha}')
