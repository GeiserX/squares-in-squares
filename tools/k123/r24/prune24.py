import pathlib,json,re,os,signal,time
R=pathlib.Path.home()/'scratch/squares-k123';producer=int((R/'worker.pids').read_text().splitlines()[3]);os.kill(producer,signal.SIGSTOP)
try:
 lines=(R/'queue.tsv').read_text().splitlines();old={tuple(x) for x in json.load(open(R/'old-completed.json'))};seen=set();kept=[];counts={};cache={}
 for l in lines:
  w=l.split('\t')
  if len(w)!=8:counts['malformed']=counts.get('malformed',0)+1;continue
  n,tag,pool=int(w[0]),w[1],w[7]
  if pool.startswith('fresh') and int(pool[5:])<10000 and (n,tag) in old:counts['old-completed']=counts.get('old-completed',0)+1;continue
  if pool not in cache:
   try:cache[pool]=json.load(open(R/('sources-'+pool+'.json')))
   except Exception:cache[pool]={}
  ns=re.match(r'(\d+)r?-(\d+)r?-j',tag).groups();m=cache[pool]
  key=(n,tag,*(m.get(nn,{}).get('sha256_geometry',pool+':'+nn) for nn in ns))
  if key in seen:counts['identical-inputs']=counts.get('identical-inputs',0)+1;continue
  seen.add(key);kept.append(l)
 stamp=time.strftime('%Y%m%dT%H%M%S',time.gmtime());(R/f'queue-before-{stamp}.tsv').write_text('\n'.join(lines)+'\n');(R/'queue-prune.tmp').write_text('\n'.join(kept)+'\n');(R/'queue-prune.tmp').replace(R/'queue.tsv')
 result=dict(time=stamp,before=len(lines),after=len(kept),removed=counts);(R/f'prune-{stamp}.json').write_text(json.dumps(result));print(json.dumps(result))
finally:os.kill(producer,signal.SIGCONT)
