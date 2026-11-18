"""Round 32 kick table: every boxE job of work/boxE32/done (kind, tier from sel32.json, kick steps, tool)."""
import json, sys
from pathlib import Path
W=Path(__file__).parent;out=open(sys.argv[1],'w')
sel={o['n']:o for o in json.load(open(W/'sel32.json'))['ok']}
out.write('n\trun\tseed\ttries\tstart_side\tbest_side\tbar_score\tside_removed\tstop\tseconds\tsource\tlicence\n')
rows=[]
for p in sorted((W/'boxE32/done').glob('*.json')):
 j=json.load(open(p))
 if 'start_side' not in j:continue
 kind='control' if j.get('control') else ('leg %d'%j['legs'] if j.get('legs') else 'extra seed' if j['seed'] in (3301,3302) else
  'first 900 s kick' if j.get('tool')!='lkick' else 'first lkick, tier %s'%sel.get(j['n'],{}).get('tier','?'))
 tool=('midm_scan.py --modes lkick,kick %d s, no probe'%j['seconds']) if j.get('tool')!='lkick' else ('invent_rest.py lkick %d s'%j['seconds'])
 if j.get('sigs'):tool+=', --sigs '+j['sigs']
 rows.append((j['n'],j['tag'],j['seed'],j['tries'],j['start_side'],j['best'],j['bar'],'%.3e'%(j['start_side']-j['best']),j.get('why',''),j.get('seconds_used',''),
  '%s: %s of %s (sha256 %s), %s'%(kind,tool,j['start'],j.get('start_sha256','')[:16],'a control start' if j.get('control') else 'the held round 31 b row (results/%s)'%j.get('held_src','')),
  'control' if j.get('control') else 'ours (held round 31 b row)'))
for r in sorted(rows,key=lambda r:(r[0],r[2])):out.write('\t'.join(['%.12f'%x if isinstance(x,float) else str(x) for x in r])+'\n')
print(len(rows))
