"""Round 32 twoshort queue extension (revived agent, about 12:25Z). The sel32 plan (tiers 0 to 2, 95 rows) runs dry near 13:45Z
while the search runs to 16:55Z. Add a second 150 s lkick seed of held rows whose one earlier invent_rest lkick (any lane,
rounds 29 to 31) found nothing that changed the row: midm.md measured 2 of 11 second kicks of rows with no first find
certifying, and border's round 31 second 900 s seeds gave 494 and 864 after a first seed found nothing.
New order: tiers 0 and 1 (as before), tier 3a (last lkick line in round 29 or 30, row unchanged since: oldest first),
tier 2 (shared or p/q side fraction, 0 of about 20 in round 31), tier 3b (last lkick line in round 31), tier 4 (3a or 3b rows
with a shared or p/q side fraction). Same filters as sel32: board gap over 1e-9, no closed form, no plain public source,
no banned source. Rows another lane lkicked in round 32 stay out (the collector skips lkick claims of any age)."""
import csv, re, json, glob, sys
csv.field_size_limit(16000000)
from pathlib import Path
W=Path(__file__).parent;B=Path('$SCRATCH/bounties-squares');R=Path('results')
sel=json.load(open(W/'t3/sel32-orig.json'));ok=sel['ok'];done={o['n'] for o in ok}
lk={}
for rd in (29,30,31,32):
  for line in open(B/('handoff-r%d.log'%rd),errors='replace'):
    if 'midm_scan' in line: continue
    if re.search(r'invent_rest|invent lkick|\blkick \(',line) or re.match(r'\S+ (backlog|invent) -> \S+ claims? ',line):
      ns=set(int(m) for m in re.findall(r'\bn ?= ?(\d+)',line))
      ns|=set(int(m) for m in re.findall(r'(?:held\w*|take-[\w-]+-r\d+)/(\d+)\.csv',line))
      ns|=set(int(m) for m in re.findall(r'starts/(\d+)-',line))
      for m in re.findall(r'\bn=((?:\d+,)+\d+)',line): ns|=set(int(x) for x in m.split(','))
      for n in ns: lk[n]=max(lk.get(n,0),rd)
ch={}
for rd in (29,30,31):
  for f in glob.glob(str(R/('round%d-best-*.tsv'%rd))):
    for r in csv.DictReader(open(f),delimiter='\t'):
      try: ch[int(r['n'])]=max(ch.get(int(r['n']),0),rd)
      except (ValueError,TypeError): pass
t3a=[];t3b=[];t4=[]
for o in sel['all']:
  n=o['n']
  if n in done or n not in lk or lk[n]>=32: continue
  if [w for w in o['why'] if not w.startswith('lkick line')]: continue
  q=dict(o);q['lk_round']=lk[n];q['ch_round']=ch.get(n,0)
  q['note']='second lkick seed: the last invent_rest lkick line naming n=%d is in round %d and the held row did not change after it; board score gap %.2e'%(n,lk[n],o['gap'])
  if o['shared']: q['tier']=4;t4.append(q)
  elif lk[n]<=30: q['tier']='3a';t3a.append(q)
  else: q['tier']='3b';t3b.append(q)
key=lambda o:(o['lk_round'],-o['gap'])
t3a.sort(key=key);t3b.sort(key=key);t4.sort(key=key)
new=[o for o in ok if o['tier'] in (0,1)]+t3a+[o for o in ok if o['tier']==2]+t3b+t4
assert len(new)==len(ok)+len(t3a)+len(t3b)+len(t4)
tmp=W/'sel32.json.tmp';json.dump(dict(ok=new,all=sel['all']),open(tmp,'w'),indent=1);tmp.replace(W/'sel32.json')
print('ok was',len(ok),'now',len(new),'t3a',len(t3a),'t3b',len(t3b),'t4',len(t4))
print('t3a',[o['n'] for o in t3a]);print('t3b',[o['n'] for o in t3b][:60]);print('t4',[o['n'] for o in t4])
