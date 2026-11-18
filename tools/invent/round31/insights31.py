"""Build next-round advice from completed receipts and the final retained rows."""
import csv,json,pathlib,re,datetime,math
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent

def load(p,default=None):
 try:return json.load(open(p))
 except (OSError,ValueError):return default

def insights():
 jobs=load(W/'jobs.json',[]);byid={j['id']:j for j in jobs};base={int(r['n']):float(r['bar'])for r in csv.DictReader(open(S/'round31-briefs/bar31.tsv'),delimiter='\t')}
 stats={};ends=[]
 for j in jobs:
  if j['kind']=='control':continue
  d=load(W/'boxE-raw'/j['id']/'done.json',{})
  if not d:continue
  ends.append((j,d));c=stats.setdefault(j['kind'],dict(completed=0,moved=0,retained=0,gain=0.0));c['completed']+=1
  if d.get('new')is not None and j['side']-(d['new']+1)*math.sqrt(j['n'])>1e-8:c['moved']+=1
 for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
  ids=re.findall(r'/boxE-raw/([^/]+)/done\.json',r['source']);j=byid.get(ids[-1])if ids else None
  if j:
   c=stats[j['kind']];c['retained']+=1;c['gain']+=float(r['gain'])
 notes=[];nexts=[]
 held=stats.get('held',dict(completed=0,retained=0,gain=0))
 nexts.append(f"Kick changed held rows and held geometries without a recent kick first. This round held starts ended {held['completed']} jobs and retained {held['retained']} rows for {held['gain']:.12g}. Keep exact-byte claims and the 120-second dry probe.")
 fresh=stats.get('fresh',dict(completed=0,moved=0,retained=0))
 nexts.append(f"Use changed rectangles, joins and prepared endpoints. Stop unchanged returns to a held floor. Fresh starts moved in {fresh['moved']} of {fresh['completed']} completed jobs and retained {fresh['retained']} rows this round. Give qualifying own endpoints priority over above-bar movement.")
 repeat=[(j,d)for j,d in ends if j['n']==421 and j['kind']in('leg','deep')]
 if repeat:
  reductions=[j['side']-(d['new']+1)*math.sqrt(421)for j,d in repeat if d.get('new')is not None]
  notes.append(f"The 421 endpoint received {len(repeat)} follow seeds. Their largest certified side reduction was {max(reductions,default=0):.12g}. The first 421 scan found at 8 seconds and made its largest step at 291 seconds, so the early-find probe correctly kept it running.")
  if max(reductions,default=0)<1e-8:nexts.append('Keep the unchanged 421 endpoint closed until its geometry changes. Its family follow and two further fq seeds returned no certified side reduction above 1e-8.')
 for j,d in ends:
  if j['id'].startswith('fresh694-'):
   qs=d.get('candidate_quenches',[]);valid=[(i,x)for i,x in enumerate(qs)if x.get('new')is not None]
   if not valid:continue
   i,best=min(valid,key=lambda pair:pair[1]['new']);first=qs[0].get('new')
   elapsed=(datetime.datetime.fromisoformat(d['ended'].replace('Z','+00:00'))-datetime.datetime.fromisoformat(d['started'].replace('Z','+00:00'))).total_seconds()
   delta=(first-best['new'])if first is not None else None;gap=best['new']-base[694]
   notes.append(f"The 694 batch ended {len(qs)} candidate attempts in {elapsed:.0f} seconds. Candidate {i+1} gave the best quenched score. Its advantage over the first candidate was {delta!r}; its score minus bar31 was {gap:.12g}. Bounded candidate failures: {sum('error'in item for item in qs)}. Completed candidates remained available.")
   nexts.append(f"Keep candidate comparison bounded and measure its cost. The 694 winner was candidate {i+1} of {len(qs)}, so minimum certified side alone missed it. The batch took {elapsed:.0f} seconds and still finished {gap:.12g} above bar31.")
   break
 nexts.append('Preserve full byte-bound source walks and test shared-reader interfaces before admission. The submitted-held archive cut restored valid source checks. The three-to-four-field share update briefly stalled intake. Per-input errors now defer that input, and direct814 remains a negative control.')
 return notes,nexts
