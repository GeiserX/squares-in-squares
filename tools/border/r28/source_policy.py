from pathlib import Path
import sys,importlib.util,json,re,csv,hashlib,os,math
W=Path(__file__).parent;S=W.parent.parent
L=Path('.')
sys.path.insert(0,str(L));sys.path.insert(0,str(W))
spec=importlib.util.spec_from_file_location('border_soft_source_policy',L/'tools/softround/policy.py');soft=importlib.util.module_from_spec(spec);spec.loader.exec_module(soft)
RELAXED=set()  # r25: Samanyu-seed rows are out, no relaxed group
# r27: the Samanyu rule is lifted (round 27 brief item 2). The imported soft policy (and forensics_policy under it)
# still marks Samanyu text as seeds or unknown, so every text it reads is renamed first; samanyu1808 (CC0/Apache
# Kaggle datasets) is kept as it is. 'seed merged0' and every other check are unchanged.
def SAN(t):return re.sub(r'(?i)samanyu(?!1808)','ownseedr27',t)
_soft_table=soft.source_table
soft.source_table=lambda token:{k:SAN(v) for k,v in _soft_table(token).items()}
OLD22=soft.old_scores()
from provenance import metadata

def classify(source,licence='',proof=None):
 source=SAN(source);licence=SAN(licence)
 if proof is not None:proof=json.loads(SAN(json.dumps(proof)))
 result=soft.classify(source,licence,proof)
 # r28: the soft policy's LIFTED flag (soft r27, 22:38Z) turns every refused status into 'none', unresolved ancestry
 # and 'seed merged0' included. SAN() above already lifts the Samanyu text, so whatever status is left is restored.
 if isinstance(result.get('samanyu'),dict) and result['samanyu'].get('status','none')!='none':
  result['status']=result['samanyu']['status'];result['seeds']=result['samanyu'].get('seeds',[])
 def weak_leaf(value):
  if isinstance(value,list):return any(weak_leaf(v) for v in value)
  if not isinstance(value,dict):return False
  rec=value.get('record');children=any(value.get(k) for k in ('parents','parent','origin','reader_parent','immutable_parent','pinned_parent'))
  if isinstance(rec,dict) and not children and value.get('reason')=='recorded ancestry' and not rec.get('reader_evidence'):
   text=json.dumps(rec)
   own=bool(re.search(r'our own design|own construction|taper enumeration',text,re.I))
   named=[x for x in re.findall(r'(?<![/\w])([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+)',text) if not x.startswith(('results/','take-','work/','near/','Volumes/','Users/','gate/')) and not x.endswith(('.csv','.tsv','.json'))]
   if not own and not named:return True
  return any(weak_leaf(v) for k,v in value.items() if k!='record')
 if result['status']!='unknown' and proof and weak_leaf(proof):result.update(status='unknown',reason='generic leaf notice has no named public or own root')
 # r26: the full parent tree, bare file names included, must avoid every excluded source of the brief.
 from provenance import bad
 why=bad(source+' '+licence+' '+(json.dumps(proof) if proof is not None else ''))
 if why:result.update(status='unknown',reason='excluded ancestry r26: '+why)
 return result
def label(policy):return soft.label(policy)
def manifest_policy(r):
 source=r['donor_source'];licence=r.get('donor_licence','');proof=None
 import forensics_sources
 key=hashlib.sha256((source+licence+hashlib.sha256(Path(r['near']).read_bytes()).hexdigest()).encode()).hexdigest()
 folder=W/'policy-evidence';folder.mkdir(exist_ok=True);saved=folder/(key+'.json')
 if saved.exists():
  try:proof=json.load(open(saved))
  except (ValueError,OSError):pass
 if proof is None:
  p=Path(source.split(', ',1)[0])
  try:
   if p.exists() and p.read_bytes()==Path(r['near']).read_bytes():
    ok,ev=forensics_sources.trace(p,int(r['donor']),S)
    if ok:proof=ev
    else:
     md=metadata(p)
     if isinstance(md,dict) and md.get('reader_evidence'):proof=md['reader_evidence']
  except (OSError,ValueError,KeyError,RecursionError):pass
  if proof is None:
   # Older manifests already retain the exact descriptor read beside this donor.
   # Materialize it with a byte-identical CSV under a source-specific key.
   recorded=None
   for match in re.finditer(r'recorded ancestry ',source):
    try:
     value,_=json.JSONDecoder().raw_decode(source[match.end():])
     if isinstance(value,dict) and int(value.get('n',r['donor']))==int(r['donor']):recorded=value
    except (ValueError,TypeError):pass
   if recorded is None and '{' in source:
    try:
     value,_=json.JSONDecoder().raw_decode(source[source.index('{'):])
     if isinstance(value,dict) and all(k in value for k in ('A','B')):recorded=dict(parts=value,n=int(r['donor']))
    except ValueError:pass
   if recorded is not None and 'end' in recorded:
    rows=list(csv.DictReader(open(r['near'])))
    hh=[.5*(abs(math.cos(float(q['angle'])))+abs(math.sin(float(q['angle'])))) for q in rows]
    side=max(max(float(q[k])+h for q,h in zip(rows,hh))-min(float(q[k])-h for q,h in zip(rows,hh)) for k in ('x','y'))
    if len(rows)!=int(r['donor']) or not math.isfinite(float(recorded['end'])) or abs(side-float(recorded['end']))>1e-6:recorded=None
   if recorded is not None:
    inputs=W/'policy-inputs';inputs.mkdir(exist_ok=True);packing=inputs/(key+'.csv')
    if not packing.exists():packing.write_bytes(Path(r['near']).read_bytes())
    assert packing.read_bytes()==Path(r['near']).read_bytes()
    desc=dict(recorded);desc['retained_donor_sha256']=hashlib.sha256(packing.read_bytes()).hexdigest()
    packing.with_suffix('.json').write_text(json.dumps(desc))
    try:
     ok,ev=forensics_sources.trace(packing,int(r['donor']),S)
     if ok:proof=ev
    except (OSError,ValueError,KeyError,RecursionError):pass
  if proof is not None:
   tmp=saved.with_name(saved.name+f'.{os.getpid()}.tmp');tmp.write_text(json.dumps(proof));tmp.replace(saved)
 result=classify(source,licence,proof)
 if proof is None:
  # r27 (r26 next item 2): when forensics_sources.trace fails but the provenance.audit walk of the donor (bare
  # names, take rows and near parents) is clean and the text names a clean root, the classification stands.
  from provenance import audit_manifest
  if not(result['status']=='none' and audit_manifest(r)):result.update(status='unknown',reason='full immutable parent evidence unavailable')
  else:result['reason']=(result.get('reason') or '')+'; forensics trace unavailable, provenance.audit walk clean (r27)'
 else:result['evidence_file']=str(saved)
 return result

def root_notices(policy):
 files=list((L/'results').glob('round*-best-*.tsv'));archive=S/'take-soft-r24/work/candidate-a-sources.tsv'
 if archive.exists():files.append(archive)
 token=tuple((str(p),p.stat().st_mtime_ns) for p in files)
 table=soft.source_table(token)
 return ['source-policy root n='+str(n)+': '+table[n] for n in policy.get('roots',[]) if n in table]

def eligible(n,score,policy,candidate,current,clean):
 if policy['status']!='none':return False
 if n in RELAXED and policy['status']=='none':return score<min(OLD22[n],clean[n])-1e-10
 return score<min(candidate[n],float(current[n]['new']))-1e-10

if __name__=='__main__':
 import base28 as base25
 _,candidate,note=base25.base()
 a=classify('our own design: zone_search.py taper enumeration','our own')
 b=classify('Samanyu-dev/squares_in_squares (donor n = 365)','no licence')
 c=classify('held: seed merged0','see README')
 assert a['status']=='none' and c['status']=='unknown'
 d=classify('our own design: zone_search.py taper enumeration','our own',{'parents':[{'record':'stair-c near miss of n = 921 (921-29e12ff3.csv)'}]})
 e=classify('our own design: zone_search.py taper enumeration','CC0: Public Domain; Samanyu-dev seed ancestry: no')
 f=classify('k123_join.py 747r-921h.C','our own design')
 assert b['status']=='none' and d['status']=='none' and e['status']=='none' and f['status']=='none'
 g=classify('our own design','CC BY-SA 4.0');h=classify('prvsiyan/squares-verified-best-of-1105 n=600','ours');i=classify('held: seed merged0','see README')
 assert g['status']!='none' and h['status']!='none' and i['status']=='unknown'
 print('r28 (soft LIFTED undone, SAN kept): Samanyu donor, bare 29e12ff3 parent and 747r join now clean; CC BY-SA, the prvsiyan file and seed merged0 still refused')
 n=735;below=candidate[n]-1e-9;above=candidate[n]+1e-9;cur={n:{'new':str(candidate[n])}}
 assert eligible(n,below,a,candidate,cur,{}) and not eligible(n,above,a,candidate,cur,{})
 assert eligible(n,below,b,candidate,cur,{}) and not eligible(n,below,c,candidate,cur,{})
 print('source-policy control r28: own root below bar accepted, above bar refused; Samanyu seed accepted; unresolved refused; base',note)
