from common28 import *
import fcntl
collector_lock=open(W/'collect.lock','a')
fcntl.flock(collector_lock,fcntl.LOCK_EX)
try:subprocess.run([sys.executable,str(W/'autoaccept28.py')],timeout=160,check=False)
except Exception as e:print('AUTO_ERROR',repr(e),flush=True)
subprocess.run([sys.executable,str(W/'withdraw28.py')],timeout=20,check=True)
base,bar,label=bar();take={int(r['n']):r for r in rows(T/'take.tsv')};seen=set(read(W/'collected.json',[]))
for n,r in list(take.items()):
 text=r['source']+' '+r['licence']
 for ap in (W/'audited').glob('*.json'):
  au=read(ap,{})
  if au.get('accepted') and au.get('n')==n:text+=' '+json.dumps(au)+' '+json.dumps(read(au.get('input_proof') or '',{}))
 hit=next((p for p in read(W/'source-holds.json',{}) if p in text),None)
 if hit:
  shutil.move(T/f'{n}.csv',W/f'{n}-withdrawn-parent.csv');del take[n];hand(f'WITHDRAW {T}/{n}.csv; parent '+hit);note(f'WITHDRAW n{n} parent '+hit);continue
 if float(r['new'])>=bar[n]-1e-10:
  dst=T/'near'/f'{n}-superseded.csv';shutil.copy2(T/f'{n}.csv',dst);atomic(dst.with_suffix('.json'),dict(source_override=r['source'],licence_override=r['licence'],superseded_by=bar[n]));(T/f'{n}.csv').unlink();del take[n];note(f'RETIRE {n} lower live score{bar[n]}')
# Round 26 15:25Z: the way back from RETIRE. A retired row returns when the take that beat it is gone
# (twoshort dropped its 415 at 14:55Z) and the row is again below the live bar by more than 1e-10.
for sp in sorted((T/'near').glob('*-superseded.csv')):
 n=int(sp.name.split('-')[0]);meta=read(sp.with_suffix('.json'),{})
 if not meta.get('source_override') or n not in bar:continue
 # 15:52Z: floatsafe of every superseded file each loop pushed collect past its 180 s limit; cache the score by file hash.
 cache=read(W/'superseded-scores.json',{});h=hashlib.sha256(sp.read_bytes()).hexdigest()
 if h in cache and (cache[h] is None or cache[h]>=bar[n]-1e-10):continue
 fr=[{k:r[k] for k in CSV} for r in csv.DictReader(open(sp))];score=cache.get(h);why='retired certified row'
 if score is None:
  import light28 as M;score=M.side(M.load(str(sp),{n})[n])/math.sqrt(n)-1
 cache[h]=None if fr is None else score;atomic(W/'superseded-scores.json',cache)
 if fr is None or score>=bar[n]-1e-10:continue
 if n in take and score>=float(take[n]['new'])-1e-10-1e-12:continue
 with open(T/f'{n}.csv.tmp','w',newline='') as h:w=csv.DictWriter(h,fieldnames=CSV);w.writeheader();w.writerows(fr)
 os.replace(T/f'{n}.csv.tmp',T/f'{n}.csv')
 src=meta['source_override'];src=src if src.startswith('reinstated') else 'reinstated after the live take that beat it left; '+src
 take[n]=dict(zip(COL,[n,repr(base[n]),repr(score),repr(base[n]-score),src,meta['licence_override']]))
 with open(T/'take.tsv.tmp','w',newline='') as h:w=csv.DictWriter(h,fieldnames=COL,delimiter='\t');w.writeheader();w.writerows(take[k] for k in sorted(take))
 os.replace(T/'take.tsv.tmp',T/'take.tsv');hand(f'certified n={n} score={score!r} gain={base[n]-score!r} (reinstated: the take that beat it left), {T}/{n}.csv');note(f'REINSTATE n{n} score{score} from {sp.name}; live bar {bar[n]}')
for host in ['boxE','boxD']:
 for d in (W/host/'out').glob('*'):
  if not d.is_dir() or not (d/'DONE').exists() or not d.name.startswith(('final-','near-')):continue
  key=host+'-'+d.name
  if key in seen:continue
  if d.name.split('-',1)[1] in read(W/'prohibited-tags.json',[]):
   seen.add(key);continue
  for p in d.glob('*.csv'):
   n=int(p.stem);j=read(p.with_suffix('.json'),{});score=j['finish_score'];tag=d.name.split('-',1)[1]
   sha=tag[1:13];proof=next((W/'ancestry').glob(sha+'*.json'),None)
   if proof is None:proof=read(W/'audited'/f'{tag}.json',{}).get('input_proof')
   a=read(proof,{}) if proof else {}
   record=dict(n=n,score=score,base=base[n],live_bar=bar[n],output=str(p),finish=j,proof=str(proof),host=host)
   if n in take and score>=float(take[n]['new'])-1e-10:
    seen.add(key)
    stale=W/'prospective'/f'{n}-{tag}.json'
    if stale.exists():stale.unlink()
    continue
   if score<bar[n]-1e-10:
    prospective=W/'prospective'/f'{n}-{tag}.json';atomic(prospective,record)
    audit=read(W/'audited'/f'{tag}.json',{})
    if audit.get('accepted') is False:
     seen.add(key);note(f'AUDIT_REFUSED n{n} {tag} '+str(audit.get('reason',''))[:240])
     dest=W/'source-withheld';dest.mkdir(exist_ok=True)
     if prospective.exists():shutil.move(prospective,dest/prospective.name)
     continue
    if not audit.get('accepted'):note(f'PROSPECTIVE n{n} score{score} gain{base[n]-score} needs complete ancestry {prospective}');continue
    from ancestor_share28 import inspect as ancestor_check
    parent_proof=rproof=audit.get('input_proof') or (str(proof) if proof else None)
    if not parent_proof:note('WITHHELD '+tag+' no immutable ancestor proof');continue
    anc=ancestor_check(parent_proof)
    if anc['excluded'] or anc['errors']:
     audit.update(accepted=False,reason='pinned ancestor share exclusion or unresolved geometry',ancestor_share_check=anc);atomic(W/'audited'/f'{tag}.json',audit);seen.add(key);note('REFUSED ancestor guard '+tag+' '+json.dumps(anc['excluded'])[:1000]);continue
    audit['ancestor_share_check']=anc
    holdtext=json.dumps([a,audit],sort_keys=True)
    holds=read(W/'source-holds.json',{})
    hit=next((p for p in holds if p in holdtext),None)
    if hit:note('REFUSED '+tag+' active parent withdrawal '+hit);seen.add(key);continue
    if not j.get('finish_quenched'):note('WITHHELD '+tag+' unquenched');continue
    from prvsim28 import check
    inputs=list((W/'inputs').glob(f'{n}-{tag}.csv'))
    if len(inputs)!=1:note('WITHHELD '+tag+' missing input snapshot');continue
    fr=[{k:r[k] for k in CSV} for r in csv.DictReader(open(p))];why='remote classfill_finish certified at 2.2e-11 before and after quench'
    if fr is None or score>=bar[n]-1e-10:note(f'REFUSED {tag} {why}');seen.add(key);continue
    if n in take and score>=float(take[n]['new'])-1e-10:seen.add(key);continue
    log=W/host/'logs'/(tag+'.log');qlines=[l for l in log.read_text().splitlines() if 'quench:' in l or ' QUENCH ' in l]
    if not qlines:note('WITHHELD '+tag+' missing completed quench log');continue
    audit['certified_output_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
    audit['quench_receipt']=dict(host=host,log=str(log),line=qlines[-1],finish_quenched=True,passes=j.get('finish_quench_passes'))
    atomic(W/'audited'/f'{tag}.json',audit)
    with open(T/f'{n}.csv.tmp','w',newline='') as h:w=csv.DictWriter(h,fieldnames=CSV);w.writeheader();w.writerows(fr)
    os.replace(T/f'{n}.csv.tmp',T/f'{n}.csv')
    take[n]=dict(zip(COL,[n,repr(base[n]),repr(score),repr(base[n]-score),'kick strengths '+str(j.get('finish_kicks','0.02'))+' and certified-file fq quench on '+host+'; '+audit['source']+'; ancestry '+str(W/'audited'/f'{tag}.json'),audit['licence']]))
    # Publish the table before announcing the row.
    with open(T/'take.tsv.tmp','w',newline='') as h:w=csv.DictWriter(h,fieldnames=COL,delimiter='\t');w.writeheader();w.writerows(take[n] for n in sorted(take))
    os.replace(T/'take.tsv.tmp',T/'take.tsv');hand(f'certified n={n} score={score!r} gain={base[n]-score!r}, {T}/{n}.csv');note(f'CERTIFIED n{n} {tag} score{score}')
    accepted=W/'accepted-candidates';accepted.mkdir(exist_ok=True)
    if prospective.exists():shutil.move(prospective,accepted/prospective.name)
   else:
    dst=W/'near-unproved'/f'{n}-{tag}.csv';dst.parent.mkdir(exist_ok=True);shutil.copy2(p,dst);atomic(dst.with_suffix('.json'),record)
   seen.add(key)
for n,r in take.items():
 r['held']=repr(base[n]);r['gain']=repr(base[n]-float(r['new']))
 from source_credits28 import attach
 sha=hashlib.sha256((T/f'{n}.csv').read_bytes()).hexdigest()
 aa=next((read(p,{}) for p in (W/'audited').glob('*.json') if read(p,{}).get('accepted') and read(p,{}).get('certified_output_sha256')==sha),None)
 if aa and aa.get('input_proof'):attach(r,aa['input_proof'])
with open(T/'take.tsv.tmp','w',newline='') as h:w=csv.DictWriter(h,fieldnames=COL,delimiter='\t');w.writeheader();w.writerows(take[n] for n in sorted(take))
os.replace(T/'take.tsv.tmp',T/'take.tsv');atomic(W/'collected.json',sorted(seen))
relayed=set(read(W/'worker-events.json',[]))
for host in ['boxE','boxD']:
 for p in (W/host/'logs').glob('worker-*.log'):
  for line in p.read_text().splitlines():
   key=host+' '+line
   if key in relayed:continue
   if any(v in line for v in ['START ','DONE ','WORKER_STOP']):relayed.add(key);note('WORKER_EVENT '+key+' log '+str(p)+' deadline05:45Z')
atomic(W/'worker-events.json',sorted(relayed));print('TAKE',len(take),'gain',sum(base[n]-float(r['new']) for n,r in take.items()),flush=True)
# Round 26: copy close certified misses to near/ for the follow lanes (near28.py, its own sidecars).
try:subprocess.run([sys.executable,str(W/'near28.py')],timeout=120,check=False)
except Exception as e:print('NEAR_ERROR',repr(e),flush=True)
