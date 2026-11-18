"""Round 31 kick table: every boxE job of work/boxE31/done, in the columns of the round 26 table plus the probe."""
import json, sys, math, csv
from pathlib import Path
W=Path(__file__).parent;out=open(sys.argv[1],'w')
out.write('n\trun\tseed\ttries\tstart_side\tbest_side\tbar_score\tside_removed\tstop\tseconds\tsource\tlicence\n')
rows=[]
for p in sorted((W/'boxE31/done').glob('*.json')):
 j=json.load(open(p))
 if 'start_side' not in j:continue
 kind='control' if j.get('control') else ('leg %d'%j.get('legs',0) if j.get('legs') else 'after a dry midm probe' if j['tag'].startswith('ab-') else 'first kick')
 rows.append((j['n'],j['tag'],j['seed'],j['tries'],j['start_side'],j['best'],j['bar'],'%.3e'%(j['start_side']-j['best']),j.get('why',''),j.get('seconds_used',''),
  '%s: %s %d s of %s (sha256 %s), the held round 30 c row (results/%s)'%(kind,'invent_rest.py lkick' if j.get('tool')=='lkick' else 'midm_scan.py lkick,kick (probe %s s)'%j.get('probe'),j['seconds'],j['start'],j.get('start_sha256','')[:16],j.get('held_src','')),
  'ours (held round 30 c row)'))
for r in sorted(rows,key=lambda r:(r[0],r[2])):out.write('\t'.join(['%.12f'%x if isinstance(x,float) else str(x) for x in r])+'\n')
print(len(rows))
