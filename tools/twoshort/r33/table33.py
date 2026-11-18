"""Round 33 kick table: every boxE job of work/boxE33/done (control, follow, first lkick, deep 900 s kick, leg)."""
import json, sys
from pathlib import Path
W=Path(__file__).parent;out=open(sys.argv[1],'w')
out.write('n\trun\tseed\ttries\tstart_side\tbest_side\tbar_score\tside_removed\tstop\tseconds\tsource\tlicence\n')
rows=[]
for p in sorted((W/'boxE33/done').glob('*.json')):
 j=json.load(open(p))
 if 'start_side' not in j:continue
 t=j['tag']
 kind='control' if j.get('control') else ('leg %d'%j['legs'] if j.get('legs') else 'follow lkick' if t.startswith('f33') else 'first lkick of a held row (n 400 to 1000)' if t.startswith('held33') else 'deep queue: one unprobed 900 s kick seed')
 tool=('midm_scan.py --modes lkick,kick %d s, %s'%(j['seconds'],'no probe' if not j.get('probe') else 'probe %d s'%j['probe'])) if j.get('tool')!='lkick' else ('invent_rest.py lkick %d s'%j['seconds'])
 fo=j.get('follow',{})
 what='a control start' if j.get('control') else ('the held round 32 a row' if j.get('held') else 'take-%s-r33/%d.csv'%(fo.get('lane'),j['n']))
 lic='control' if j.get('control') else (fo.get('licence','')[:200] or 'ours')
 rows.append((j['n'],t,j['seed'],j['tries'],j['start_side'],j['best'],j['bar'],'%.3e'%(j['start_side']-j['best']),j.get('why',''),j.get('seconds_used',''),
  '%s: %s of %s (sha256 %s), %s'%(kind,tool,j['start'],j.get('start_sha256','')[:16],what),lic))
for r in sorted(rows,key=lambda r:(r[0],r[2])):out.write('\t'.join(['%.12f'%x if isinstance(x,float) else str(x) for x in r])+'\n')
print(len(rows))
