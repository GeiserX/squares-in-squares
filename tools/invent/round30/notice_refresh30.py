"""Exercise live notice selection and cache invalidation on frozen source evidence."""
import json
import os
import pathlib
import sys
import tempfile

W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r30/work')
sys.path.insert(0,str(W))
import controller28 as C
import source_gate28 as G

G._walker_stamp=(C.R/'quench_walk.py').stat().st_mtime_ns
job=next(j for j in json.loads((W/'jobs.json').read_text())if j['id']=='recover641')
job=dict(job,id='control-notice-refresh30')
endpoint=W/'boxE-raw/recover641/final/641.csv'
assert G.check(job,endpoint)['clean'],'actual recovered641 must pass first'
evidence=json.loads(pathlib.Path(job['evidence']).read_text())
snap=next(s for s in evidence['snapshots']if '/take-'in s['original']and s['original'].endswith('.csv'))
original_logs=G.handoff_logs
original_loader=G.Q.load_withdrawn
original_lines=list(G.Q.WITHDRAWN_LINES)
checks={}
try:
 with tempfile.TemporaryDirectory(prefix='notice30-',dir=W)as folder:
  root=pathlib.Path(folder)
  for n in range(20,33):(root/f'handoff-r{n}.log').write_text('')
  checks['round_selection']=[p.name for p in G.handoff_logs(root)]==[f'handoff-r{n}.log'for n in range(22,31)]
  assert checks['round_selection']
  log=root/'handoff-r30.log'
  G.handoff_logs=lambda:[log]
  loader_calls=[]
  G.Q.load_withdrawn=lambda:loader_calls.append(True)
  G.Q.WITHDRAWN_LINES.clear()
  G._notice_stamps={};G._withdraw_stamp=None
  checks['empty_notice_passes']=G.check(job,endpoint)['clean']
  stamp=log.stat().st_mtime_ns
  def write(text):
   global stamp
   log.write_text(text)
   stamp+=1_000_000
   os.utime(log,ns=(stamp,stamp))
  prefix='2026-11-15T18:00:00Z invent -> all: WITHDRAW n641 source missing '
  wrong='0'*64 if snap['sha256']!='0'*64 else '1'*64
  write(prefix+snap['original']+' sha256='+wrong+'\n')
  checks['wrong_pin_passes']=G.check(job,endpoint)['clean']
  write(prefix+snap['original']+' sha256='+snap['sha256']+'\n')
  refused=G.check(job,endpoint)
  checks['new_exact_notice_refuses']=not refused['clean']and any('withdrawal 'in h for h in refused['hits'])
  with log.open('a')as stream:
   stream.write('2026-11-15T18:00:01Z invent -> all: REINSTATE '+snap['original']+' sha256='+snap['sha256']+'\n')
  os.utime(log,ns=(stamp+1_000_000,stamp+1_000_000))
  checks['new_exact_reinstatement_passes']=G.check(job,endpoint)['clean']
  checks['withdrawal_loader_refreshed']=len(loader_calls)==4
  assert all(checks.values()),checks
finally:
 G.handoff_logs=original_logs
 G.Q.load_withdrawn=original_loader
 G.Q.WITHDRAWN_LINES[:]=original_lines
 G._notice_stamps={};G._withdraw_stamp=None
checks['actual_source_still_passes']=G.check(job,endpoint)['clean']
assert all(checks.values()),checks
(W/'notice-refresh-control.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks))
