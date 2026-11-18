"""Change the initial side on measured moving ends that stalled above the bar."""
import csv,hashlib,json,math,pathlib,sys,time
W=pathlib.Path(__file__).resolve().parent;S=W.parents[1]
sys.path.insert(0,str(W));import controller28 as C
G=C.G
old=S/'take-invent-r29/work'
rows=json.load(open(old/'measurement.json'))['rows'];jobs={j['id']:j for j in json.load(open(old/'jobs.json'))}
bar,peer=C.bars();picked=[];counts=set()
for row in sorted(rows,key=lambda r:(r['end_side']-(peer[r['n']]+1)*math.sqrt(r['n'])) if r.get('end_side')else 99):
 if row['kind']!='near'or not row['source_ok']or not row.get('side_gain')or row['side_gain']<1e-6:continue
 n=row['n'];delta=row['end_side']-(peer[n]+1)*math.sqrt(n)
 if n in counts or delta<1e-7 or delta>.002:continue
 counts.add(n);picked.append(row)
 if len(picked)==6:break
for row in picked:
 n=row['n'];prior=jobs[row['id']];p=old/'boxE-raw'/prior['id']/'final'/f'{n}.csv'
 ident=f'b30x{n}x{prior["id"]}';done=W/'bar-admissions'/f'{ident}.json';done.parent.mkdir(exist_ok=True)
 if done.exists():continue
 payload=p.read_bytes();digest=hashlib.sha256(payload).hexdigest()
 graph=json.load(open(prior['ancestry']))
 node=dict(source='own local kick and family squeeze r29, exact output '+str(p)+' sha256 '+digest,licence='our own construction; upstream sources in parent graph',record=str(p),parents=[graph['root']])
 key=hashlib.sha256(json.dumps(node,sort_keys=True).encode()).hexdigest();graph=dict(graph,nodes=dict(graph['nodes']),root=key,path=str(p));graph['nodes'][key]=node
 graphpath=W/'ancestry'/f'{ident}.json';graphpath.write_text(json.dumps(graph,separators=(',',':')))
 result=G.freeze(p,n,str(graphpath))
 done.write_text(json.dumps(result,indent=2))
 if not result['clean']:
  C.state('BAR ADMISSION held n='+str(n)+' '+str(result['hits'])[:1000]);continue
 start='starts/'+ident+'.csv';(W/start).write_bytes(payload)
 job=dict(id=ident,n=n,start=start,seconds=900,seed=123,kind='barretry',program='invent_bar30.py',fq=prior['fq'],bar=(peer[n]+1)*math.sqrt(n),side=row['end_side'],order=row['end_side']-(peer[n]+1)*math.sqrt(n),ancestry=str(graphpath),input_sha256=digest,evidence=result['path'],evidence_sha256=result['sha256'],priority=-1.4,options=[],bar_parent=prior['id'])
 extra=C.load(W/'extra-ready.json',[]);extra.append(job);C.atomic(W/'extra-ready.json',extra)
 C.state('QUEUE changed bar-side mechanism '+ident+' n='+str(n)+', prior side move '+str(row['side_gain'])+', delta '+str(job['order'])+'; old unchanged geometry receives a new compressed initial side. Requires BAR_CONTROL_GREEN, common17:45Z')
 print(ident,job['order'],flush=True)
