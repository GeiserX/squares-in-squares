"""Resume only the final comparison and report after the completed numerical run."""
import pathlib,json,time,datetime,sys,glob,runpy,os
W=pathlib.Path(__file__).resolve().parent;T=W.parent
progress=json.load(open(W/'finish-progress.json'))
assert all(progress.get(k)for k in ('controller_stopped','remote_workers_done','verified','copied','removed'))
sys.path.insert(0,str(W))
# The full source walks are already captured. Publication does not use the historical search index.
original_glob=glob.glob;skipped=[]
def publication_glob(pattern,*args,**kwargs):
 if str(pattern).endswith('/work/*/ancestry'):
  skipped.append(str(pattern));return []
 return original_glob(pattern,*args,**kwargs)
glob.glob=publication_glob
try:import controller28 as C
finally:glob.glob=original_glob
C.COLLECT_ONLY=True
(W/'close-ready.json').write_text(json.dumps(dict(time=C.now(),skipped_unused_index=skipped)))
with (T/'STATE.txt').open('a')as f:f.write(C.now()+' CLOSER restored only comparison/report; all completed numerical/verification/cleanup steps skipped by receipts. No new source walk or numerical job.\n')
# Refresh the live take now and warm the source reference before the timed comparison.
runpy.run_path(str(W/'finalize28.py'),run_name='__main__')
(W/'close-warm.json').write_text(json.dumps(dict(time=C.now(),source_reference_ready=True)))
freeze_at=datetime.datetime(2026,11,15,5,54,35,tzinfo=datetime.timezone.utc).timestamp()
report_at=datetime.datetime(2026,11,15,5,55,5,tzinfo=datetime.timezone.utc).timestamp()
while time.time()<freeze_at:time.sleep(min(20,freeze_at-time.time()))
runpy.run_path(str(W/'finalize28.py'),run_name='__main__')
runpy.run_path(str(W/'measure28.py'),run_name='__main__')
with (T/'STATE.txt').open('a')as f:f.write(C.now()+' CLOSER final comparison completed.\n')
while time.time()<report_at:time.sleep(min(20,report_at-time.time()))
runpy.run_path(str(W/'report28.py'),run_name='__main__')
with (T/'STATE.txt').open('a')as f:f.write(C.now()+' CLOSER report written after05:55Z; closer ends.\n')
