"""Check recorded first-public sources against immutable source snapshots."""
import csv,hashlib,io,json,pathlib,re,sys
R=pathlib.Path('.');W=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(W));sys.path.insert(0,str(R));import forensics_public29 as P;import forensics_watch as F

def gather(parts):
 rows=F.gather_notices(parts)
 for row in rows:
  if int(row['n'])==801:row.update(source='own construction: canonical held801 packing',licence='our own construction')
 return rows

DROP={'prvsiyan_shares','prvsiyan_share','prvsiyan_share_check','ancestor_share_check','original_seed_shares','original_seed_share_checks','share_checks','complete_parent_share_audit','controls','control','negative_controls','positive_controls','excluded','rejected','policy','public_roots'}
def pruned(value):
 if isinstance(value,dict):return {k:pruned(v)for k,v in value.items()if k not in DROP}
 if isinstance(value,list):return [pruned(v)for v in value]
 return value

def audit(evidence,ancestry):
 ev=json.load(open(evidence));proof=pruned(json.load(open(ancestry)));public=P.reader()
 files={};texts={};counts={};terms={};held_by_hash={};documents=[];implicit={}
 for snap in ev['snapshots']:
  p=pathlib.Path(snap['path'])
  if hashlib.sha256(p.read_bytes()).hexdigest()!=snap['sha256']:raise ValueError('changed frozen public-source evidence')
  original=snap['original'];files[original]=str(p);files[str(p)]=str(p)
  if p.suffix=='.json':
   try:value=pruned(json.loads(p.read_text()))
   except ValueError:continue
   texts[original]=json.dumps(value);documents.append(value)
 root=proof.get('nodes',{}).get(proof.get('root'),{})
 snapshot=next((v for v in ev['snapshots']if v['sha256']==ev['input_sha256']and v['path'].endswith('.csv')),None)
 if snapshot:
  proof=dict(proof,path=snapshot['path'],n=ev['n'],record=dict(source=root.get('source',''),licence=root.get('licence',''),public_first=ev.get('public_first',False)))
 def visit(v):
  if isinstance(v,dict):
   path=v.get('path');n=v.get('n');digest=v.get('snapshot_sha256')
   if path and isinstance(n,int)and str(path).endswith('.csv'):
    path=str(path);counts[(path,n)]=path
    record=v.get('record')
    if isinstance(record,dict):texts[path+'.json']=json.dumps(record);texts[path]=str(record.get('source',''))
    if digest and '/gather/'in path:
     notices=gather({'root':dict(source=[path,n])})
     if notices:held_by_hash[digest]=notices[0]
   for key,child in v.items():
    if key!='record':visit(child)
  elif isinstance(v,list):
   for child in v:visit(child)
 visit(proof)
 for document in documents:visit(document)
 # Bind retained origin aliases to their captured bytes, never a later path build.
 for snap in ev['snapshots']:
  if not snap['original'].endswith('.csv'):continue
  for suffix in ('.origin.json','.json'):
   raw=texts.get(snap['original']+suffix)
   if raw is None:continue
   origin=json.loads(raw)
   if not isinstance(origin,dict):continue
   original=origin.get('path');n=origin.get('n')
   if original and n and origin.get('snapshot_sha256')==snap['sha256']:
    files[str(original)]=snap['path'];counts[(str(original),int(n))]=str(original)
 # A simple held reference may carry its source as text rather than an origin
 # object. Audit the fetched archive row, without measuring the held packing.
 from implicit_public29 import capture
 root_held={(int(n),int(r))for n,r in re.findall(r'held n\s*=\s*(\d+)\s+of round\s*(\d+)',root.get('source',''),re.I)}
 for label,notice in ev.get('texts',[]):
  held=re.fullmatch(r'held (\d+) (\d+)',str(label))
  if not held or(int(held[1]),int(held[2]))not in root_held or not public.direct_public(notice.split(' || ',1)[0]):continue
  item=capture(notice,int(held[1]));original=item['original'];files[original]=item['path'];counts[(original,int(held[1]))]=original
  texts[original]=item['source'];texts[original+'.json']=json.dumps(dict(n=int(held[1]),source=item['source'],licence=item['licence'],public_first=True));terms[original]=item['licence']+' '+item['source'];implicit[original]=item
 nodes={};folder=W/'public-root-snapshots';folder.mkdir(exist_ok=True)
 for (original,n),_ in counts.items():
  logical=original;actual=files.get(original)
  if '/gather/'in original:
   held=gather({'root':dict(source=[original,n])})
   if not held or not public.direct_public(held[0].get('source','')):continue
   logical=original[:-4]+'.n%d.csv'%n;texts[logical]=held[0]['source'];terms[logical]=held[0].get('licence','')+' '+held[0]['source']
   texts[logical+'.json']=json.dumps(dict(n=n,source=held[0]['source'],licence=held[0].get('licence','')))
  if not public.public_node(logical,n,texts,files):continue
  if not actual:
   # A recorded public ancestor must have immutable bytes, even if still live.
   raise ValueError('public-first ancestor has no captured bytes: '+original)
  if logical not in terms:
   for name in(original+'.json',original+'.origin.json',original[:-4]+'.json'):
    raw=texts.get(name)
    if raw is None:continue
    data=json.loads(raw)
    if isinstance(data,dict):
     terms[logical]=' '.join(str(data.get(k,''))for k in('licence','licence_text','source'))
     if any(token in terms[logical]for token in('Apache','CC0','CC BY 4.0')):break
  path=pathlib.Path(actual);parsed=public.packing(path)
  if parsed is None:
   with path.open()as stream:rows=[r for r in csv.DictReader(stream)if int(r['n'])==n]
   if len(rows)!=n:raise ValueError('public-first ancestor count missing: '+original)
   stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=['n','x','y'],extrasaction='ignore');writer.writeheader();writer.writerows(rows);payload=stream.getvalue().encode();key=hashlib.sha256(payload).hexdigest();path=folder/(key+'.csv')
   if not path.exists():path.write_bytes(payload)
  key=hashlib.sha256(path.read_bytes()).hexdigest();nodes[(logical,key)]=(logical,str(path),key)
 rows=public.audit_nodes(list(nodes.values()),texts,files)
 for row in rows:
  notice=terms.get(row['original'],'');inherited=held_by_hash.get(row['sha256'])
  if inherited and not any(t in notice for t in('Apache','CC0','CC BY 4.0','Attribution 4.0')):
   notice=inherited.get('licence','')+' '+inherited.get('source','');row['held_source']=inherited
  held_other=('/gather/'in row['original']or inherited is not None or row['original']in implicit)and 'Other'in notice
  permitted=bool(re.search(r'Apache[- ]*(?:License\s*,?\s*(?:Version\s*)?)?2(?:\.0)?|CC0|Public\s*Domain|(?:CC[- ]*BY[- ]*|Attribution\s+)4\.0',notice,re.I))
  if re.search(r'CC[ -]BY[ -]SA|CC[ -]BY[ -]NC|ShareAlike|NonCommercial',notice,re.I):permitted=False;held_other=False
  if row['original']in implicit:row['captured_public_archive']=implicit[row['original']]
  row.update(licence_notice=notice,held_other_exception=held_other,licence_allowed=permitted or held_other,allowed=row['share1e3']<.4 and(permitted or held_other))
 return dict(clean=all(r['allowed']for r in rows),public_roots=rows)

if __name__=='__main__':
 try:result=audit(sys.argv[1],sys.argv[2])
 except Exception as error:result=dict(clean=False,public_roots=[],error=repr(error))
 pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(dict(clean=result['clean'],public_roots=len(result['public_roots']),bad=[{k:r[k]for k in('n','original','share1e3','licence_allowed')}for r in result['public_roots']if not r['allowed']],error=result.get('error'))),flush=True)
