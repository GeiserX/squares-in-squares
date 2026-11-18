"""Rule n stop: kill a running or queued job of n when a live peer row at n is more than 1e-6 of score below
min(bar36, the job's own start). Cases tested by control()."""
import json,csv,math,pathlib,subprocess,sys
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r36/work'
def should_stop(bar,start,live):return live<min(bar,start)-1e-6
def control():
 b=0.02
 assert not should_stop(b,b+1e-5,b)        # donor above the bar, live row at the bar: no stop
 assert should_stop(b,b+1e-5,b-2e-6)       # donor, live row 2e-6 below the bar: stop
 assert should_stop(b,b,b-2e-6)            # held start, live row 2e-6 below: stop
 assert not should_stop(b,b,b)             # held start alone: no stop
 return 'guard control 4/4'
if __name__=='__main__':
 print(control())
 sys.path.insert(0,str(W/'tools'))
 bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round36-briefs/bar36.tsv'),delimiter='\t')}
 live={}
 for p in S.glob('take-*-r36/take.tsv'):
  if 'invent' in p.parent.name:continue
  try:
   for r in csv.DictReader(open(p),delimiter='\t'):live[int(r['n'])]=min(live.get(int(r['n']),9),float(r['new']))
  except Exception:pass
 kills=[]
 for j in json.load(open(W/'jobs.json')):
  n=j['n'];st=j['side']/math.sqrt(n)-1
  if n in live and should_stop(bar[n],st,live[n]) and not (W/'boxE/runs'/j['id']/'done.json').exists():kills.append(j['id'])
 if kills:
  subprocess.run(['ssh','boxE','cd $SCRATCH/squares-invent-r36 && touch '+' '.join('kill/'+k for k in kills)],check=False)
  # a queued job is skipped by the worker only through done.json; drop killed jobs from the queue too
  q=json.load(open(W/'boxE/queue.json'));q=[j for j in q if j['id'] not in kills]
  json.dump(q,open(W/'boxE/queue.json.tmp','w'));(W/'boxE/queue.json.tmp').replace(W/'boxE/queue.json')
  print('KILL',kills)
