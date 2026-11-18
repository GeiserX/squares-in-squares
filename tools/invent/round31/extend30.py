"""Bind a certified own endpoint to its complete frozen input source walk."""
import csv,hashlib,json,math,pathlib,sys,time
W=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(W))

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def verified_end(path,n,receipt,certified,marker):
 path=pathlib.Path(path);certified=pathlib.Path(certified);marker=pathlib.Path(marker)
 if not receipt.get('quench_from_certified'):raise ValueError('endpoint has no completed certified-input quench')
 if not math.isfinite(float(receipt['new']))or receipt['clearance']<2.2e-11:raise ValueError('endpoint receipt has no finite certified score')
 rows=list(csv.DictReader(path.open()))
 if len(rows)!=n or any(int(row['n'])!=n for row in rows):raise ValueError('endpoint packing count mismatch')
 if sha(path)!=receipt['sha256']:raise ValueError('endpoint differs from completed receipt')
 if sha(certified)!=receipt['quench_input_sha256']or marker.read_text().strip()!=receipt['quench_input_sha256']:raise ValueError('certified-input quench byte identity mismatch')
 return receipt['sha256']

def extend(parent,path,n,ancestry):
 import source_gate28 as G
 path=pathlib.Path(path)
 folder=W/'boxE-raw'/parent['id']
 if path.resolve()!=(folder/'final'/f'{n}.csv').resolve():return dict(clean=False,hits=['endpoint is not the named worker final file'])
 original=W/parent['start'];ep=pathlib.Path(parent['evidence'])
 if sha(ep)!=parent['evidence_sha256']:return dict(clean=False,hits=['changed parent source evidence'])
 current=G.check(parent,original)
 if not current['clean']:return dict(clean=False,hits=current['hits'])
 old=json.load(ep.open());graph=json.load(open(ancestry))
 if not old['clean']or sha(ancestry)!=old['ancestry_sha256']or not graph['ok']or graph['policy']!='strict28v1' or graph['n']!=n:return dict(clean=False,hits=['frozen parent graph does not match its evidence'])
 for pin in old['snapshots']:
  if not pathlib.Path(pin['path']).is_file()or sha(pin['path'])!=pin['sha256']:return dict(clean=False,hits=['changed frozen parent pin '+pin['original']])
 rp=folder/'done.json';receipt=json.load(rp.open());cert=folder/'certin'/f'{n}.csv';marker=folder/'quench'/f'{n}.done'
 try:digest=verified_end(path,n,receipt,cert,marker)
 except (OSError,ValueError,KeyError,TypeError)as error:return dict(clean=False,hits=[str(error)])
 if receipt['id']!=parent['id']:return dict(clean=False,hits=['endpoint worker receipt id differs'])
 # The prior graph remains intact. A new own operation names that exact root.
 operation=dict(source='our own construction: '+receipt.get('program','local search')+' completed worker endpoint; certified-input fq receipt '+str(rp)+' sha256 '+sha(rp),licence='our own construction',record=str(rp)+' n='+str(n),parents=[graph['root']])
 root=hashlib.sha256(json.dumps(dict(operation=operation,input=digest),sort_keys=True).encode()).hexdigest()
 graph['nodes'][root]=operation;graph.update(root=root,path=str(path),ok=True,reason='certified own endpoint extends complete frozen input walk')
 body=json.dumps(graph,separators=(',',':')).encode();graphsha=hashlib.sha256(body).hexdigest()
 ap=W/'ancestry'/('extended-'+graphsha+'.json');ap.parent.mkdir(exist_ok=True)
 if ap.exists()and ap.read_bytes()!=body:raise ValueError('changed endpoint graph at content-addressed path')
 if not ap.exists():ap.write_bytes(body)
 pins=W/'pins';pins.mkdir(exist_ok=True);snapshots=list(old['snapshots'])
 for original in(path,rp,cert,marker,ep,ap):
  raw=original.read_bytes();key=hashlib.sha256(raw).hexdigest();snapshot=pins/(key+original.suffix)
  if snapshot.exists()and snapshot.read_bytes()!=raw:raise ValueError('changed content-addressed endpoint pin')
  if not snapshot.exists():snapshot.write_bytes(raw)
  item=dict(original=str(original),path=str(snapshot),sha256=key,original_mtime_ns=original.stat().st_mtime_ns)
  if not any(v['original']==item['original']and v['sha256']==key for v in snapshots):snapshots.append(item)
 texts=list(old['texts']);texts.extend([(str(path),''),(str(rp),rp.read_text()),(str(ap),body.decode())])
 value=dict(old,policy='own-source-r30-extended-endpoint',input_sha256=digest,n=n,ancestry=str(ap),ancestry_sha256=graphsha,snapshots=snapshots,texts=texts,public_first=False,clean=True,hits=[],time=time.strftime('%FT%TZ',time.gmtime()),extension=dict(parent_evidence=str(ep),parent_evidence_sha256=parent['evidence_sha256'],parent_job=parent['id'],worker_receipt=str(rp),worker_receipt_sha256=sha(rp)))
 key=hashlib.sha256((parent['evidence_sha256']+digest+graphsha+sha(rp)).encode()).hexdigest();out=W/'evidence'/('extended-'+key+'.json')
 if not out.exists():out.write_text(json.dumps(value,separators=(',',':')))
 evsha=sha(out);checked=G.check(dict(id='extension-'+key[:12],n=n,evidence=str(out),evidence_sha256=evsha,ancestry=str(ap)),path)
 return dict(clean=checked['clean'],hits=checked['hits'],path=str(out),sha256=evsha,ancestry=str(ap),parent_pins=len(old['snapshots']))

if __name__=='__main__':
 jobs=json.load(open(W/'jobs.json'));parent=next(j for j in jobs if j['id']==sys.argv[1]);n=parent['n']
 result=extend(parent,W/'boxE-raw'/parent['id']/'final'/f'{n}.csv',n,parent['ancestry'])
 print(json.dumps(result))
