import json,pathlib,time,sys
w=pathlib.Path(__file__).resolve().parent;until=float((w/'report-deadline').read_text())+120
while time.time()<until:
 try:
  jobs=json.load(open(w/'jobs.json'));done=[];active=[]
  for j in jobs:
   p=w/'boxE-raw'/j['id']/'done.json'
   if p.exists():
    if j['kind']!='control':done.append((j,json.load(open(p))))
   elif (w/'boxE-raw/locks'/j['id']).exists():active.append(j['n'])
  c=json.load(open(w/'comparison.json'));declines=sum(d.get('search_end')=='dry-probe'for j,d in done);errors=[j['id']for j,d in done if d.get('error')]
  print(time.strftime('%FT%TZ',time.gmtime()),'ended',len(done),'dry_probes',declines,'active',active,'retained',c['improved_n'],'gain',c['gain']['against_base_bar'],'errors',errors,flush=True)
  if(w.parent/'report.json').exists():print('REPORT_READY',flush=True);break
 except Exception as e:print('monitor',str(e),flush=True)
 time.sleep(50)
