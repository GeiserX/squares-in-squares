"""Recover only interrupted, unreported jobs from the lost boxE wrapper pool."""
from pathlib import Path
import json,re,time,subprocess,hashlib,sys
R=Path.home()/'scratch/squares-k123';cut=(R/'boxE_guard33.py.pid').stat().st_mtime-1;apply='--apply' in sys.argv;events=[];done={};allrows=[]
for wd in (R/'out').glob('j22*'):
 p=wd/'done.jsonl'
 if p.exists():
  for l in p.read_text().splitlines():
   try:r=json.loads(l);allrows.append(r);done.setdefault(wd.name,set()).add(r['pool']+'-'+str(r['n'])+'-'+r['tag'])
   except (ValueError,KeyError):pass
ps=subprocess.check_output(['ps','-axo','command'],text=True);queue=[l.split('\t') for l in (R/'queue.tsv').read_text().splitlines() if len(l.split('\t'))>=8]
for worker in ['j22a','j22b','j22c','j22w']:
 wd=R/'out'/worker
 if not wd.is_dir():continue
 for D in sorted(wd.iterdir()):
  if not D.is_dir() or D.name in done.get(worker,set()) or D.stat().st_mtime>=cut or str(D)+'/' in ps:continue
  mt=re.fullmatch(r'(.+?)-(\d+)-((\d+)r?-(\d+)r?-j.*)',D.name)
  if not mt:continue
  pool,nn,tag,x,y=mt.groups();n=int(nn);mechanism='loosen1.005-r30' if worker=='j22w' else 'standard';raws=list((D/'raw').glob('*.csv'));event={'worker':worker,'pool':pool,'n':n,'tag':tag,'raws':len(raws)}
  if raws:
   event['action']='recover_raw_record'
   if apply:
    record={'worker':worker,'pool':pool,'n':n,'tag':tag,'bar':next(float(w[4]) for w in queue if w[7]==pool and w[0]==nn and w[1]==tag),'raw':len(raws),'recovered_interruption33':True,'mechanism':mechanism}
    with (wd/'done.jsonl').open('a') as h:h.write(json.dumps(record)+'\n')
   events.append(event);continue
  if any(z['pool']==pool and z['tag']==tag and z.get('mechanism','standard')==mechanism for z in allrows):event['action']='keep_closed_completed_geometry';events.append(event);continue
  meta=json.load((R/('sources-'+pool+'.json')).open());roots=[(k,meta[k]['sha256_geometry'],meta[k].get('ancestry_sha256','')) for k in [x,y]];claims=[]
  for w in queue:
   if w[7]!=pool or w[0]!=nn or w[1]!=tag:continue
   sig=hashlib.sha256(json.dumps([tag,w[3],roots]+([mechanism] if mechanism!='standard' else []),sort_keys=True).encode()).hexdigest();p=R/'claims'/('input-'+sig)
   if p.is_dir() and not list(p.iterdir()):
    claims.append(p.name)
    if apply:
     target=R/'interrupted-claims33'/p.name;target.parent.mkdir(exist_ok=True);assert not target.exists();p.rename(target)
  event.update(action='reopen_interrupted_unreported_recipe' if claims else 'no_matching_claim',claims=claims);events.append(event)
receipt={'time':time.strftime('%FT%TZ',time.gmtime()),'applied':apply,'cutoff':cut,'events':events};(R/('interrupted-recovery33.json' if apply else 'interrupted-review33.json')).write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
