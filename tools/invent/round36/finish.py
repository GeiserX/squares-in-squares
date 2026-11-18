"""Scan pulled runs/*/done.json; for each certified final below bar36 and every live r36 take by more than 1e-10,
re-certify locally (finesafe), write <n>.csv + sidecar into the take dir, and rewrite take.tsv by rename.
Moved finds that stay above the live bar go to near/ (with sidecar). Prints a summary line per run."""
import json,csv,glob,math,pathlib,sys,hashlib,time,shutil,os
S=pathlib.Path('$SCRATCH/bounties-squares');T=S/'take-invent-r36';W=T/'work'
sys.path.insert(0,str(W/'boxE'));sys.path.insert(0,'.')
from certify31 import certify
def now():return time.strftime('%FT%TZ',time.gmtime())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round36-briefs/bar36.tsv'),delimiter='\t')}
def peers():
 b={}
 for p in S.glob('take-*-r36/take.tsv'):
  if p.parent==T:continue
  try:
   for r in csv.DictReader(open(p),delimiter='\t'):
    n=int(r['n']);v=float(r['new'])
    if v<b.get(n,(9,''))[0]:b[n]=(v,p.parent.name)
  except Exception:pass
 return b
jobs={j['id']:j for j in json.load(open(W/'jobs.json'))}
take={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')} if (T/'take.tsv').exists() else {}
pe=peers();seen=json.load(open(W/'finished.json')) if (W/'finished.json').exists() else {}
changed=False
for d in sorted(glob.glob(str(W/'boxE/runs/*/done.json'))):
 r=json.load(open(d));jid=r['id'];j=jobs.get(jid)
 if j is None:continue
 n=r['n'];key=jid+':'+str(r.get('sha256'))
 if key in seen:continue
 line=dict(id=jid,n=n,error=r.get('error'),raw=r.get('raw'),new=r.get('new'),ok=r.get('certified_ok'))
 if r.get('new') is not None:
  line['vs_bar']=r['new']-bar[n];line['start_vs_bar']=(j['side']/math.sqrt(n)-1)-bar[n]
 f=W/'boxE/runs'/jid/'final'/f'{n}.csv'
 if r.get('certified_ok') and f.exists() and r['new']<bar[n]-1e-10:
  v=certify(f,n)
  if v is None:line['local']='refused by local finesafe'
  else:
   sc=v[2];line['local']=sc;p=pe.get(n,(9,''))
   own=float(take[n]['new']) if n in take else 9
   if sc<bar[n]-1e-10 and sc<p[0]-1e-10 and sc<own:
    out=T/f'{n}.csv'
    with open(str(out)+'.tmp','w',newline='') as h:
     w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows([{k:x[k] for k in w.fieldnames} for x in v[1]])
    os.replace(str(out)+'.tmp',out)
    src=f"invent round36: {j['program']} {j.get('modes','lkick') if j['program']!='midm' else 'midm_scan.py lkick,kick'} 900 s seed {j['seed']} job {jid}; start {j['origin']} sha256 {j['input_sha256']} (its own sidecar holds its recorded source); certified with finesafe 2.2e-11 and the full fq loop (midm_fqonce.py) from the certified file on boxE"
    side=dict(n=n,source=src,licence='own layout built from the start named in source (see its sidecar)',start=j['origin'],start_sha256=j['input_sha256'],parent=j['origin'],sha256=sha(out),time=now())
    json.dump(side,open(str(out)+'.json','w'))
    take[n]=dict(n=n,held=bar[n],new=sc,gain=bar[n]-sc,source=src,licence='own layout; start: '+j['origin'])
    changed=True;line['take']=True
    with open(T/'STATE.txt','a') as h:h.write(f"{now()} boxA CERTIFIED n={n} score {sc!r} gain {bar[n]-sc:.3e} vs bar36, below live peers ({p[1] or 'none'}); {out}; walk pending\n")
   else:line['lost_to']=p
 elif r.get('certified_ok') and f.exists() and r['new']<line['start_vs_bar']+bar[n]-1e-9:
  q=T/'near'/f'{n}-{jid}.csv';shutil.copyfile(f,q)
  json.dump(dict(n=n,source=f"invent round36 near: job {jid} final, start {j['origin']} sha256 {j['input_sha256']}",parent=j['origin'],sha256=sha(q)),open(str(q)+'.json','w'))
  line['near']=str(q)
 seen[key]=line;print(json.dumps(line))
json.dump(seen,open(W/'finished.json','w'))
if changed:
 with open(T/'take.tsv.tmp','w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader()
  for n in sorted(take):w.writerow({k:take[n][k] for k in w.fieldnames})
 os.replace(T/'take.tsv.tmp',T/'take.tsv')
