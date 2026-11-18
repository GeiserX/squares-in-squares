import pathlib,json,csv,math,collections
W=pathlib.Path(__file__).resolve().parent;T=W.parent;R=pathlib.Path('.')
J=json.load(open(W/'jobs.json'));out=[];summary=collections.defaultdict(lambda:dict(attempts=0,normal=0,moved=0,tries=0,side_gain=0.0,clean_attempts=0,clean_normal=0,clean_moved=0,clean_tries=0,clean_side_gain=0.0))
for j in J:
 p=W/'boxE-raw'/j['id'];d=json.load(open(p/'done.json'))if(p/'done.json').exists()else{}
 ts=[]
 for f in p.glob('slide-*.tsv'):
  ts += [l.split('\t')for l in f.read_text().splitlines()if l and not l.startswith('#')and l.split('\t')[0].isdigit()]
 newside=(d['new']+1)*math.sqrt(j['n'])if 'new'in d else None
 proof=json.load(open(j['ancestry']))if j.get('ancestry')else{}
 source_ok=bool(proof.get('ok'))and proof.get('policy')=='strict27v1'
 independent_path=W/'independent-results'/f'{j["id"]}.json'
 independent=json.load(open(independent_path))if independent_path.exists()else None
 row=dict(independent_source_checked=independent is not None,independent_source_ok=bool(independent.get('clean'))if independent else None,id=j['id'],n=j['n'],kind=j['kind'],seconds=j['seconds'],seed=j['seed'],fq=j['fq'],start_side=j['side'],end_side=newside,side_gain=j['side']-newside if newside else None,tries=len(ts),started=d.get('started',''),ended=d.get('ended',''),error=d.get('error',''),ancestry=j.get('ancestry','control'),input_sha256=j.get('input_sha256',''),old_id=j.get('old_id',''),source_ok=source_ok,source_policy=proof.get('policy',''),source_reason=proof.get('reason','control'),quench_from_certified=bool(d.get('quench_from_certified')))
 out.append(row)
 if d and j['kind']!='control':
  v=summary[j['kind']];v['attempts']+=1;v['tries']+=len(ts)
  if source_ok:v['clean_attempts']+=1;v['clean_tries']+=len(ts)
  if d.get('quench_from_certified') or d.get('raw')==0:
   v['normal']+=1
   if source_ok:v['clean_normal']+=1
   if source_ok and row['side_gain'] and row['side_gain']>1e-8:v['clean_moved']+=1;v['clean_side_gain']+=row['side_gain']
   if row['side_gain'] and row['side_gain']>1e-8:v['moved']+=1;v['side_gain']+=row['side_gain']
with (W/'measure.tsv').open('w',newline='')as h:
 w=csv.DictWriter(h,fieldnames=list(out[0]),delimiter='\t');w.writeheader();w.writerows(out)
(W/'measurement.json').write_text(json.dumps(dict(summary=summary,started=sum(bool(r['started'])for r in out),ended=sum(bool(r['ended'])for r in out),total_tries=sum(r['tries']for r in out),rows=out),indent=2))
print(json.dumps(dict(summary=summary,ended=sum(bool(r['ended'])for r in out),tries=sum(r['tries']for r in out))))
