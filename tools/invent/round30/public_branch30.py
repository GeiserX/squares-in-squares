"""Audit direct public parents while cutting only the submitted-held paths."""
import csv,hashlib,io,json,pathlib,re,sys
W=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('.')
sys.path.insert(0,str(R/'tools/harvest30'))
import common
common.W=W/'branch-work';common.W.mkdir(exist_ok=True)
common.T=W.parent
import walk as H
import public_sources as P
from held_paths import audit as audit_paths,direct_nodes
sys.path.insert(0,str(W))
import public_roots29 as L
L.P.reader=lambda:P

def source_object(source):
 pos=source.find('{')
 if pos<0:return {}
 for value in (source[pos:],source[pos:].replace('\\"','"')):
  try:return json.JSONDecoder().raw_decode(value)[0]
  except ValueError:pass
 return {}

def record_path(node):return str(node.get('record','')).split(' n=',1)[0]
def count(node,default=0):
 matches=re.findall(r'\bn=(\d+)\b',str(node.get('record','')))
 if matches:return int(matches[-1])
 m=re.match(r'(\d+)[-.]',pathlib.Path(record_path(node)).name)
 return int(m[1])if m else default

PIN_HASHES={}
def known_direct(path):
 path=str(path)
 for suffix in('.origin.json','.source.json','.provenance.json','.json'):
  if path.endswith('.csv'+suffix):path=path[:-len(suffix)];break
 if path.endswith('/take-harvest-r26/814.csv')and PIN_HASHES.get(path,'').startswith('5a4c0cdb'):return True
 if path.endswith('/take-harvest-r26/695.csv'):return True
 if re.search(r'/take-forensics-r22/work/donors/799-986b3b6daebce05b9257\.csv',path):return True
 return False

def held_node(node):
 record=record_path(node);source=node.get('source','')
 if known_direct(record):return False
 if re.search(r'(?:^|/)results/round\d+-best-[^/]+\.tsv$',record):return True
 roots=source_object(source).get('pinned_snapshot_roots',[])
 if roots and all(re.search(r'(?:^|/)gather/round\d+-[^/]+\.csv$',str(v.get('path','')))for v in roots):return True
 return bool(re.match(r'^(?:fq quench of (?:the )?)?held(?: packing)?(?: of)? n\s*=',source,re.I))

def audit(evidence,ancestry):
 global PIN_HASHES
 ev=json.load(open(evidence));graph=json.load(open(ancestry))
 PIN_HASHES={pin['original']:pin['sha256']for pin in ev['snapshots']}
 hashes={pin['original']:pin['sha256']for pin in ev['snapshots']}
 files={};raw={str(k):v for k,v in ev.get('texts',[])}
 for pin in ev['snapshots']:
  p=pathlib.Path(pin['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==pin['sha256'],'changed frozen public evidence'
  files[pin['original']]=str(p);files[str(p)]=str(p)
  if p.suffix=='.json':raw.setdefault(pin['original'],json.dumps(L.pruned(json.load(open(p)))))
 # First collect public-node identities and licence notices, without a share call.
 saved=P.audit_nodes
 def metadata(nodes,texts,paths):
  result=[]
  for original,path,key in nodes:
   value=P.packing(path)
   if value is not None:result.append(dict(original=original,snapshot=path,sha256=key,n=value[0],share1e3=0.,share1e6=0.,allowed=True))
  return result
 P.audit_nodes=metadata
 try:all_rows=L.audit(evidence,ancestry)['public_roots']
 finally:P.audit_nodes=saved
 by_key={(row['original'],row['sha256']):row for row in all_rows}
 # Include the exact frozen transports named by main, even if a sidecar calls them owned.
 for pin in ev['snapshots']:
  if not pin['original'].endswith('.csv'):continue
  value=P.packing(pin['path'])
  if value is None:continue
  n=value[0];original=pin['original']
  for suffix in('.json','.origin.json','.provenance.json','.source.json'):raw.setdefault(original+suffix,'{}')
  if P.public_node(original,n,raw,files):
   by_key.setdefault((original,pin['sha256']),dict(original=original,snapshot=pin['path'],sha256=pin['sha256'],n=n,licence_notice='',licence_allowed=False))
 all_rows=list(by_key.values());texts={};unresolved=set();made={};required=[]
 prefix=W/'branch-work/views'
 def held_edge(parent,child):
  roots=source_object(parent.get('source','')).get('pinned_snapshot_roots',[])
  matches=[r for r in roots if r.get('source')==child.get('source')and r.get('licence')==child.get('licence')and int(r.get('n',0))==count(child)]
  return bool(matches)and all('/gather/round'in str(r.get('path',''))for r in matches)
 def graph_view(value):
  key=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
  if key in made:return made[key]
  names={node:str(prefix/(key+'-'+node+'.json'))for node in value['nodes']}
  made[key]=names[value['root']]
  for node_id,node in value['nodes'].items():
   label=names[node_id];record=record_path(node);record_data={}
   try:record_data=json.loads(raw.get(record,'{}'))
   except ValueError:pass
   layout=record_data.get('layout',record_data)if isinstance(record_data,dict)else{}
   incoming=[str(v)for data in(record_data,layout)if isinstance(data,dict)for k,v in data.items()if k in('path','original','original_input','input','start','csv')and isinstance(v,str)and v.endswith('.csv')]
   forced=[p for p in incoming if known_direct(p)]
   explicit_held=isinstance(layout,dict)and re.match(r'^held round\s*\d+',str(layout.get('origin','')),re.I)and layout.get('source')==node.get('source')and layout.get('licence')==node.get('licence')
   if not forced and(held_node(node)or explicit_held):texts[label]='held boundary';continue
   links=[names[p]for p in node.get('parents',[])if p in names and not held_edge(node,value['nodes'][p])]
   source=node.get('source','');links.extend(forced)
   prefix_source=source.split('{',1)[0]
   direct_prefix=re.match(r'^fq (?:follow|quench(?: check)?) of\s+([^ ;]+\.csv)',prefix_source)
   if direct_prefix and known_direct(direct_prefix[1]):links.append(direct_prefix[1])
   obj=source_object(source)
   for part in ('A','B','C'):
    ref=obj.get(part,{}).get('source')if isinstance(obj.get(part),dict)else None
    if isinstance(ref,list)and ref and known_direct(ref[0]):links.append(str(ref[0]))
   if P.direct_public(source)or known_direct(record):
    expected=count(node)or int(layout.get('n',0))or(value.get('n',0)if node_id==value['root']else 0)
    required.append((label,expected))
    if record.endswith('.csv'):links.append(record)
    elif record.endswith('.json')and record in raw:links.append(record)
    elif record.endswith('/take.tsv'):
     links.append(str(pathlib.Path(record).parent/(str(count(node))+'.csv')))
    else:
     slug=re.search(r'[\w.-]+/[\w.-]+\s*::',source)
     matches=[r for r in all_rows if r['n']==count(node,value.get('n',0))and slug and slug[0].split('::')[0].strip()in r.get('licence_notice','')]
     if len({r['sha256']for r in matches})==1:links.extend(r['original']for r in matches)
     else:unresolved.add(label)
   texts[label]=json.dumps(dict(source=source if P.direct_public(source)else'',parents=links))
  return made[key]
 def clean(value):
  if isinstance(value,dict):
   if isinstance(value.get('nodes'),dict)and value.get('root')in value['nodes']:return dict(source_graph_root=graph_view(value))
   if '/gather/round'in str(value.get('path',''))and isinstance(value.get('n'),int):return dict(held_boundary=value['n'])
   if {'original','snapshot','sha256'}.issubset(value):return dict(byte_pin_sha256=value['sha256'])
   return {k:clean(v)for k,v in value.items()if k not in('walk','walked_texts','snapshots','controls','prvsiyan_shares','complete_parent_share_audit')}
  if isinstance(value,list):return [clean(v)for v in value]
  return value
 for label,text in raw.items():
  try:texts[label]=json.dumps(clean(json.loads(text)))
  except ValueError:texts[label]=text
 root_view=graph_view(graph)
 root_snap=next((p for p in ev['snapshots']if p['sha256']==ev['input_sha256']and p['original']==graph.get('path')),None)
 root_snap=root_snap or next(p for p in ev['snapshots']if p['sha256']==ev['input_sha256']and p['path'].endswith('.csv'))
 root=root_snap['original'];root_pin=root_snap['path'];node=graph['nodes'][graph['root']]
 for label in set([root,root_pin]):
  texts[label]=json.dumps(dict(source_graph_root=root_view))
  texts[label+'.source.json']=json.dumps(dict(source=node.get('source','')if P.direct_public(node.get('source',''))else'',licence=node.get('licence',''),n=ev['n']))
  for suffix in('.json','.origin.json','.provenance.json'):texts[label+suffix]='{}'
 direct=direct_nodes(root,texts)
 for label,n in required:
  if label not in direct:continue
  reached=direct_nodes(label,texts)
  if label==root_view:reached.update((root,root_pin))
  if not any(row['original']in reached and row['n']==n for row in all_rows):unresolved.add(label)
 if unresolved&direct:raise ValueError('unresolved direct public byte identity: '+str(sorted(unresolved&direct)[:3]))
 selected=[(r['original'],r['snapshot'],r['sha256'])for r in all_rows if r['original']in direct]
 audits=P.audit_nodes(selected,texts,files)
 if all(row['allowed']for row in audits):audit_paths(root,texts,files,selected,())
 notice={(r['original'],r['sha256']):r for r in all_rows}
 for row in audits:
  meta=notice[(row['original'],row['sha256'])];row['licence_notice']=meta.get('licence_notice','');row['licence_allowed']=meta.get('licence_allowed',False)
  if not row['licence_allowed']:
   ledger=raw.get(row['original'],'')
   if ' || 'in ledger:
    terms=ledger.rsplit(' || ',1)[1]
    if re.search(r'Apache[^;]*2|CC0|CC BY 4\.0',terms)and not re.search(r'BY.SA|NonCommercial',terms,re.I):row.update(licence_notice=ledger,licence_allowed=True)
  if not row['licence_allowed']:
   for label,text in raw.items():
    if not label.endswith('.json'):continue
    try:data=json.loads(text)
    except ValueError:continue
    if not isinstance(data,dict)or data.get('original')!=row['original']or int(data.get('n',0))!=row['n']:continue
    companion=label[:-5]
    if hashes.get(companion)!=row['sha256']:continue
    terms=' '.join(str(data.get(k,''))for k in('licence','licence_text','license'))
    if re.search(r'Apache[^;]*2|CC0|CC BY 4\.0',terms)and not re.search(r'BY.SA|NonCommercial',terms,re.I):
     row.update(licence_notice=terms+' '+str(data.get('source',''))+'; byte-identical alias bound by '+label,licence_allowed=True);break
  if not row['licence_allowed']:
   for name in(row['original']+'.json',row['original']+'.origin.json',row['original']+'.source.json'):
    try:data=json.loads(raw.get(name,'{}'))
    except ValueError:continue
    terms=' '.join(str(data.get(k,''))for k in('licence','licence_text','license'))
    if re.search(r'Apache[^;]*2|CC0|CC BY 4\.0',terms)and not re.search(r'BY.SA|NonCommercial',terms,re.I):row.update(licence_notice=terms+' '+str(data.get('source','')),licence_allowed=True);break
  if meta.get('captured_public_archive'):row['captured_public_archive']=meta['captured_public_archive']
  row['allowed']=row['allowed']and row['licence_allowed']
 return dict(clean=all(r['allowed']for r in audits),public_roots=audits,direct_public_originals=[row['original']for row in audits],source_notices=[{k:v for k,v in row.items()if k in('original','captured_public_archive')}for row in all_rows if row.get('captured_public_archive')],held_only_nodes=len(all_rows)-len(selected),direct_labels=len(direct),policy='harvest30 held_paths with frozen explicit-graph views')

if __name__=='__main__':
 try:result=audit(sys.argv[1],sys.argv[2])
 except Exception as error:result=dict(clean=False,public_roots=[],error=repr(error))
 pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(dict(clean=result['clean'],error=result.get('error'),public_roots=len(result['public_roots']),held_only_nodes=result.get('held_only_nodes'))),flush=True)
