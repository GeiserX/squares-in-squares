from pathlib import Path
import json,hashlib,subprocess,time
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;inbox=W/'near-inbox36';inbox.mkdir(exist_ok=True);notes=[]
for name in ['546-prejoin31-9732905d62caa90a.csv','448-threeway28-3fcfae4dc7c761a4.csv']:
 p=T/'near'/name;meta=json.load(open(str(p)+'.json'));n=int(meta['n']);sha=hashlib.sha256(p.read_bytes()).hexdigest();key='complete-diagnostic-'+sha[:16];request=inbox/(key+'.json')
 if request.exists():continue
 remote='diagnostic-completion36/'+sha[:16];subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-k123/'+remote],check=True);subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/'+remote+f'/{n}.csv'],check=True)
 tag='verify-near36-'+key;source=f'own certified-file fq follow of {p} (sha256 {sha}); initial construction: '+meta['source']
 j={'kind':'verify','near_donor36':True,'tag':tag,'n':n,'raw':remote+f'/{n}.csv','out':'near-cert36/'+key,'source':source,'licence':meta['licence'],'producer_job':meta['numeric_job']}
 d=W/'near-cert36'/key;d.mkdir(parents=True,exist_ok=True);job=d/'job36.json';job.write_text(json.dumps(j));subprocess.run(['scp','-q',str(job),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True);subprocess.run(['ssh','boxE','mv $SCRATCH/squares-k123/tasks/'+tag+'.json.tmp $SCRATCH/squares-k123/tasks/'+tag+'.json'],check=True)
 tmp=request.with_suffix('.tmp');tmp.write_text(json.dumps({**j,'request_key':key,'status':'queued'}));tmp.replace(request);assert sha==hashlib.sha256(p.read_bytes()).hexdigest();notes.append({'initial_diagnostic':str(p),'sha256':sha,'completion_job':key})
C=W/'corrections';C.mkdir(exist_ok=True);(C/'early-diagnostic-completion36.json').write_text(json.dumps(notes,indent=2))
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: early546/448 diagnostic copies retain their exact bytes and records. Certified-file fq completion is queued through the durable near inbox; useful completed results will get separate records. They carry no take credit. '+str(C/'early-diagnostic-completion36.json')+'\n'
for p in [T/'STATE.txt',S/'handoff-r36.log']:
 with open(p,'a') as f:f.write(line)
print(json.dumps({'queued':notes,'original_bytes_unchanged':True}))
