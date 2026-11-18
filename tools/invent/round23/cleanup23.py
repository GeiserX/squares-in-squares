import pathlib,subprocess,json,hashlib,datetime,os,signal,sys
W=pathlib.Path(__file__).resolve().parent;T=W.parent
now=datetime.datetime.now(datetime.timezone.utc)
assert now>=datetime.datetime(2026,11,13,18,30,tzinfo=datetime.timezone.utc),'cleanup is allowed only after the common deadline'
for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines():
 if line.strip().endswith('Python -u '+str(W/'controller23.py')) or line.strip().endswith('python -u '+str(W/'controller23.py')):os.kill(int(line.split()[0]),signal.SIGTERM)
def ssh(code):
 p=subprocess.run(['ssh','boxE','$SCRATCH/squares-base/venv/bin/python -'],input=code,capture_output=True,text=True,timeout=60,check=True);return p.stdout
process_code='''import subprocess,json,os,signal,time,pathlib
D=pathlib.Path.home()/'scratch/squares-invent-r23'
rows={}
for l in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 a=l.strip().split(None,2)
 if len(a)==3:rows[int(a[0])]=(int(a[1]),a[2])
roots=set()
for pid in (35358,35359,35360):
 if pid not in rows:continue
 p=subprocess.run(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True)
 if ('n'+str(D)) in p.stdout.splitlines():roots.add(pid)
own=set(roots)
while True:
 more=own|{p for p,(pp,cmd)in rows.items()if pp in own}
 if more==own:break
 own=more
for pid in sorted(own,reverse=True):
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
time.sleep(1)
left=[]
for pid in own:
 p=subprocess.run(['ps','-p',str(pid),'-o','stat='],capture_output=True,text=True)
 if p.stdout.strip()and not p.stdout.strip().startswith('Z'):left.append(pid)
assert not left,left
print(json.dumps({'killed_if_present':sorted(own),'left':left}))
'''
proc=json.loads(ssh(process_code));(W/'processes-final.json').write_text(json.dumps(proc,indent=2))
args=['rsync','-a','--exclude=lane/','--exclude=starts/','--exclude=locks/','--exclude=*.py','--exclude=logs/','--exclude=tmp/','--exclude=*.tmp','boxE:scratch/squares-invent-r23/',str(W/'boxE-raw')+'/']
subprocess.run(args,check=True,timeout=90)
subprocess.run(['rsync','-a','boxE:scratch/squares-invent-r23/lane/',str(W/'deployed-lane')+'/'],check=True,timeout=60)
manifest=json.loads(ssh('''import pathlib,hashlib,json
D=pathlib.Path.home()/'scratch/squares-invent-r23';out={}
for p in D.rglob('*.csv'):
 r=p.relative_to(D)
 if 'tmp'in r.parts or r.parts[0]=='lane':continue
 out[str(r)]=hashlib.sha256(p.read_bytes()).hexdigest()
print(json.dumps(out))
'''))
bad=[]
for rel,sha in manifest.items():
 p=(W if pathlib.Path(rel).parts[0]=='starts'else W/'boxE-raw')/rel
 if not p.exists()or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:bad.append(rel)
(W/'remote-csv-manifest.json').write_text(json.dumps(manifest,indent=2))
(W/'transfer-check.json').write_text(json.dumps({'csv_count':len(manifest),'mismatches':bad},indent=2));assert not bad,bad
subprocess.run(['ssh','boxE','rm -rf -- $SCRATCH/squares-invent-r23'],check=True,timeout=30)
subprocess.run(['ssh','boxE','test ! -e $SCRATCH/squares-invent-r23'],check=True,timeout=30)
out={'processes_left':f'None. All three boxE workers and their children ended. The local collector stopped. All {len(manifest)} remote CSV hashes matched local copies before removing the lane scratch. No lane work ran on boxC or boxD.','csv_count':len(manifest)}
(W/'cleanup.json').write_text(json.dumps(out,indent=2))
with open(T/'STATE.txt','a')as h:h.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA FINISH cleanup: '+out['processes_left']+' Final bar checks use local archived final files; take freeze18:40Z.\n')
print(json.dumps(out))
