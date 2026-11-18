"""Resolve an empty origin root from its exact immutable packing record."""
import csv,hashlib,json,pathlib,re
S=pathlib.Path('$SCRATCH/bounties-squares')

def resolve(root,current,metadata):
 p=pathlib.Path(root.get('path',''));n=int(root.get('n',0))
 if not p.is_absolute():p=S/p
 match=re.search(r'/take-[a-z0-9-]+-r(\d+)/',str(p))
 if not match or int(match[1])>=30 or p==pathlib.Path(current) or not p.is_file() or p.suffix!='.csv':return None
 data=p.read_bytes();rows=list(csv.DictReader(data.decode().splitlines()))
 if len(rows)!=n:return None
 expected=root.get('snapshot_sha256')or root.get('sha256')
 if expected and hashlib.sha256(data).hexdigest()!=expected:return None
 source,licence,record=metadata(p,n)
 if source.startswith('unresolved ancestry:'):return None
 if source and licence:return source,licence,record
 # Older reopened-held records wrote the operation and exact parents, but no
 # redundant licence. Read that licence from the named accepted held rows.
 side=pathlib.Path(str(p)+'.json')
 if not source or not side.is_file():return None
 value=json.loads(side.read_text());parents=value.get('parents',[]);roots=[]
 if not parents or value.get('n')!=n:return None
 for pair in parents:
  if not isinstance(pair,list)or len(pair)!=2 or not isinstance(pair[1],int):return None
  parent=pathlib.Path(pair[0])
  if parent.parent!=S/'gather' or not re.fullmatch(r'round\d+-[^/]+\.csv',parent.name):return None
  ps,pl,pr=metadata(parent,pair[1])
  if not ps or not pl:return None
  roots.append(dict(path=str(parent),n=pair[1],source=ps,licence=pl,ledger=pr))
 return 'recorded operation '+source+'; '+json.dumps(dict(pinned_snapshot_roots=roots,proof=str(side),sha256=hashlib.sha256(side.read_bytes()).hexdigest()),separators=(',',':')),'; '.join(dict.fromkeys(v['licence']for v in roots)),str(side)


def unanchored_cycles(nodes,cycles):
 def anchored(key,seen):
  if key not in nodes or key in seen:return False
  node=nodes[key]
  if node.get('refused'):return False
  parents=node.get('parents',[])
  if not parents:return bool(node.get('source')and node.get('licence'))
  return any(anchored(parent,seen|{key})for parent in parents)
 return [cycle for cycle in cycles if not anchored(cycle['node'],set())]
