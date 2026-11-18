"""Read the local collector and worker snapshots without starting search work."""
import csv,datetime,glob,json,os,re,time
csv.field_size_limit(64*1024*1024)
W='$SCRATCH/bounties-squares/take-stair-c-r24/work'
now=datetime.datetime.now(datetime.timezone.utc)
log=W+'/logs/coordinator.log';lines=open(log).read().splitlines()
stats=next((x for x in reversed(lines) if 'fresh files' in x),'no collector totals yet')
known=set()
for name in ['approved-ancestry.json','rejected-ancestry.json']:
    if os.path.exists(W+'/'+name):known.update(json.load(open(W+'/'+name)))
pending=[]
for p in glob.glob(W+'/pending-ancestry/*.json'):
    try:
        if json.load(open(p))['proof'] not in known:pending.append(p)
    except (ValueError,KeyError):pass
problems=[]
seen=set(json.load(open(W+'/main-handoff-seen.json'))) if os.path.exists(W+'/main-handoff-seen.json') else set()
messages=[x.strip() for x in open('$SCRATCH/bounties-squares/handoff-r24.log') if 'main ->' in x or ('->' in x and 'stair-c' in x.split('->',1)[1].split(':',1)[0])]
new_messages=[x for x in messages if x not in seen]
if new_messages:problems.append('new main or directed handoff')
held={228,459,503,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990}
A={int(r['n']):float(r['L']) for r in csv.DictReader(open('$SCRATCH/bounties-squares/gate/cand-round23-1113a/details.csv'))}
B={int(r['n']):float(r['L']) for r in csv.DictReader(open('$SCRATCH/bounties-squares/gate/cand-round22-1113b/details.csv'))}
reviewed=set(json.load(open(W+'/source-policy-reviewed.json'))) if os.path.exists(W+'/source-policy-reviewed.json') else set()
policy=[]
for p in glob.glob(W+'/boxcopy/*/raw-a/*.json'):
    j=json.load(open(p));n=j['n'];side=j.get('built')
    if p not in reviewed and n in held and side is not None and not j.get('early_stage') and A[n]-3e-9<=side<B[n]-3e-9:policy.append(p)
if policy:problems.append('source-free baseline review')
if os.path.getmtime(log)<time.time()-900:problems.append('collector log stale')
for key in ['n','s']:
 p=W+'/boxcopy/'+key+'/worker.log'
 if os.path.exists(p):
  text=open(p).read().splitlines()[-12:]
  if any('Traceback' in x or x.startswith(('KeyError:','ValueError:','AssertionError')) for x in text):problems.append('worker '+key+' error')
if any('Traceback' in x for x in lines[-8:]):problems.append('collector error')
rows=list(csv.DictReader(open(W+'/../take.tsv'),delimiter='\t'))
print(json.dumps(dict(utc=now.strftime('%FT%TZ'),stats=stats,pending=pending,source_policy_candidates=policy,new_handoffs=new_messages,retained=len(rows),problems=problems,stop_monitor=now>=datetime.datetime(2026,11,13,22,13,tzinfo=datetime.timezone.utc))))
