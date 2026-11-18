"""Export an immutable endpoint after one candidate completes certified-input fq."""
import pathlib,hashlib,json,csv,time,shutil,math

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def export(root,job,index,rows,certified,marker,selected,control=False):
 import floatsafe
 root=pathlib.Path(root);n=job['n'];certified=pathlib.Path(certified);marker=pathlib.Path(marker)
 if marker.read_text().strip()!=sha(certified):raise ValueError('candidate quench marker differs from certified input')
 if len(rows)!=n or any(int(r['n'])!=n for r in rows):raise ValueError('candidate count mismatch')
 score,why=floatsafe.check(n,rows);pdscore,pdwhy=floatsafe.check(n,floatsafe.via_pandas(rows));gap=min(floatsafe.clearance(rows),floatsafe.clearance(floatsafe.via_pandas(rows)))
 if why!=pdwhy or why!='ok'or gap<2.2e-11 or not math.isfinite(score):raise ValueError('unsafe candidate checkpoint')
 ident=job['id']+'-q'+str(index);folder=root/ident
 if (folder/'done.json').exists():return ident
 for name in('final','certin','quench'):(folder/name).mkdir(parents=True,exist_ok=True)
 p=folder/'final'/f'{n}.csv'
 with p.open('w',newline='')as h:
  w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rows)
 reread=list(csv.DictReader(open(p)));s,why=floatsafe.check(n,reread)
 if why!='ok'or min(floatsafe.clearance(reread),floatsafe.clearance(floatsafe.via_pandas(reread)))<2.2e-11:raise ValueError('written candidate checkpoint unsafe')
 shutil.copyfile(certified,folder/'certin'/f'{n}.csv');shutil.copyfile(marker,folder/'quench'/f'{n}.done')
 now=time.strftime('%FT%TZ',time.gmtime())
 receipt=dict(id=ident,n=n,program=job['program'],input_sha256=job['input_sha256'],started=now,ended=now,new=s,pandas_score=pdscore,clearance=gap,sha256=sha(p),quench_input_sha256=sha(certified),quench_from_certified=True,selected=str(selected),parent_search=job['id'],candidate_index=index,search_end='candidate-checkpoint')
 early=dict(job,id=ident,kind='early',parent_search=job['id'],candidate_index=index)
 (folder/'early-job.json').write_text(json.dumps(early));tmp=folder/'done.tmp';tmp.write_text(json.dumps(receipt));tmp.replace(folder/'done.json')
 return ident

def controls(root,tag="1"):
 import floatsafe
 root=pathlib.Path(root);p=root/'control2/final/2.csv';cert=root/'control2/certin/2.csv';marker=root/'control2/quench/2.done';rows=list(csv.DictReader(open(p)))
 j=dict(id='checkpoint-control-'+str(tag),n=2,kind='control',program='control',input_sha256=sha(cert))
 ident=export(root,j,0,rows,cert,marker,p,True);assert (root/ident/'done.json').is_file()
 bad=list(map(dict,rows));bad[1]['x']=bad[0]['x'];bad[1]['y']=bad[0]['y'];bad[1]['angle']=bad[0]['angle']
 try:export(root,j,1,bad,cert,marker,p,True)
 except ValueError:pass
 else:raise AssertionError('overlap checkpoint exported')
 wrong=root/'checkpoint-wrong.done';wrong.write_text('0'*64)
 try:export(root,j,2,rows,cert,wrong,p,True)
 except ValueError:pass
 else:raise AssertionError('wrong certified-input marker exported')
 return dict(completed_candidate_exported=True,overlap_refused=True,wrong_marker_refused=True)
