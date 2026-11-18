import pathlib,time,json,csv,datetime,os
csv.field_size_limit(20000000)
W=pathlib.Path(__file__).resolve().parent;T=W.parent
while True:
 def text(name):
  try:return (W/name).read_text()
  except OSError:return ''
 rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));records=text('records.jsonl').splitlines();resident=text('resident25.log').splitlines();status={}
 for mode in ['collect','stage']:
  last=next((l for l in reversed(resident) if f' {mode} ' in l),'')
  status[mode]=last.split(' seconds=')[-1].split(' rss=')[0]+'s' if last else 'pending'
  if last:
   stamp=datetime.datetime.strptime(last.split()[0],'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=datetime.timezone.utc).timestamp();status[mode+'_age']=round(time.time()-stamp)
 notes=[]
 if (W/'controls28.json').exists():notes.append('source-controls-passed')
 if (W/'finalize26.error').exists():notes.append('FINALIZER ERROR '+text('finalize26.error'))
 print(json.dumps({'time':time.strftime('%H:%M:%SZ',time.gmtime()),'joins':len(records),'take_n':[int(r['n']) for r in rows],'gain':sum(float(r['gain']) for r in rows),**status,'notes':notes}),flush=True)
 if (T/'report.json').exists() or time.time()>float(text('deadline'))+900:break
 time.sleep(50)
