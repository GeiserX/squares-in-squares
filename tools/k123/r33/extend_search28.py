from pathlib import Path
import subprocess,os,time,datetime,json
R=Path.home()/'scratch/squares-k123';PY=Path.home()/'scratch/squares-base/venv/bin/python'
soft=datetime.datetime(2026,11,15,5,40,tzinfo=datetime.timezone.utc).timestamp()
hard=float((R/'deadline').read_text());assert soft<hard and time.time()<soft
p=R/'search-deadline';p.with_suffix('.tmp').write_text(str(soft));p.with_suffix('.tmp').replace(p)
rows=subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]
started=[];running=[]
for worker in ['j22a','j22b','j22d']:
 hits=[l.strip() for l in rows if l.strip().endswith('qrun22.py '+worker) and 'squares-base/venv/bin/python' in l]
 if hits:running.extend(hits);continue
 with (R/'out'/(worker+'-extension28.log')).open('a') as log:
  proc=subprocess.Popen(['nice','-n','5',str(PY),'-I','qrun22.py',worker],cwd=R,stdout=log,stderr=log,start_new_session=True)
 (R/(worker+'.pid')).write_text(str(proc.pid));started.append({'worker':worker,'pid':proc.pid})
report={'time':time.strftime('%FT%TZ',time.gmtime()),'search_soft':'05:40Z','common_hard':'05:45Z','already_running':running,'started':started}
(R/'search-extension28.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
