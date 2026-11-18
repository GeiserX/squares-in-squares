from pathlib import Path
import os,signal,json,time,subprocess,hashlib
W=Path(__file__).resolve().parent;S=W.parent.parent;T=W.parent;marker=W/'stop-third36';marker.touch();pid=int((W/'third.pid').read_text());cmd=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True);assert str(W/'background29.py') in cmd
# Freeze the sole near-state writer, and avoid taking a partial JSON snapshot.
for attempt in range(100):
 os.killpg(pid,signal.SIGSTOP)
 try:state=json.load(open(W/'near-state36.json'));break
 except ValueError:os.killpg(pid,signal.SIGCONT);time.sleep(.02)
else:raise RuntimeError('could not freeze a complete near-state JSON')
os.killpg(pid,signal.SIGTERM);os.killpg(pid,signal.SIGCONT)
keys=['j22a-fresh10057-793r-972-j5-25-s-3','j22a-fresh10048-793r-972-j10-10-s-3'];notes=[]
for original in keys:
 p=T/'near'/('793-'+original+'.csv');meta=json.load(open(str(p)+'.json'));before=hashlib.sha256(p.read_bytes()).hexdigest();key='complete793-'+original;D=W/'near-cert36'/key;D.mkdir(parents=True,exist_ok=True);tag='verify-near36-'+key
 j={'kind':'verify','near_donor36':True,'tag':tag,'n':793,'raw':'certs/'+original+'/out/793.csv','out':'near-cert36/'+key,'source':meta['source'],'licence':meta['licence'],'producer_job':original}
 job=D/'job36.json';job.write_text(json.dumps(j));subprocess.run(['scp','-q',str(job),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True);subprocess.run(['ssh','boxE','mv $SCRATCH/squares-k123/tasks/'+tag+'.json.tmp $SCRATCH/squares-k123/tasks/'+tag+'.json'],check=True)
 state[key]={**j,'status':'queued'};assert before==hashlib.sha256(p.read_bytes()).hexdigest();notes.append({'initial_fine_certificate':str(p),'sha256':before,'certified_file_fq_job':key,'initial_take_credit':False})
q=W/'near-state36.json.tmp';q.write_text(json.dumps(state));q.replace(W/'near-state36.json');C=W/'corrections';C.mkdir(exist_ok=True);(C/'initial-near793-clarification36.json').write_text(json.dumps(notes,indent=2))
with open(W/'third-r36.log','a') as f:p=subprocess.Popen(['nohup','nice','-n','5',str(S/'venv/bin/python'),str(W/'background29.py'),'third'],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
(W/'third.pid').write_text(str(p.pid));marker.unlink()
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: clarification: the two793 initial near files named in work/corrections/initial-near793-clarification36.json are fine certificates from the first pass. Certified-file fq is now queued for each; complete copies will have new names. They have no take credit. Their bytes and ancestry records remain unchanged; they remain owned diagnostic inputs. '+str(C/'initial-near793-clarification36.json')+'\n'
for log in [S/'handoff-r36.log',T/'STATE.txt']:
 with open(log,'a') as f:f.write(line)
print(json.dumps({'queued_originals':keys,'third_pid':p.pid,'original_bytes_unchanged':True}))
