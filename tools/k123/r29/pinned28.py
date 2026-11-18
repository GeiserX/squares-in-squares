"""Resolve a superseded producer row only through its byte-pinned original ledger."""
import pathlib,json,csv,hashlib
DEC=json.JSONDecoder()
def nodes(obj,depth=0):
 if depth>18:return
 if isinstance(obj,dict):
  yield obj
  for v in obj.values():yield from nodes(v,depth+1)
 elif isinstance(obj,list):
  for v in obj:yield from nodes(v,depth+1)
 elif isinstance(obj,str):
  # Producer source text embeds donor credit arrays after its recipe description.
  starts=[i for i,ch in enumerate(obj) if ch in '[{' and (i==0 or obj[i-1] not in '\\"')]
  for i in starts[:80]:
   try:value,_=DEC.raw_decode(obj[i:])
   except ValueError:continue
   yield from nodes(value,depth+1)
def row(path,obj):
 p=pathlib.Path(path);want=str(p);n=p.stem
 if not n.isdigit():return None
 for node in nodes(obj):
  if node.get('origin')!=want or not node.get('input_file_snapshot') or not node.get('input_file_sha256'):continue
  cp=pathlib.Path(node['input_file_snapshot']);expected=node['input_file_sha256']
  if not cp.is_file() or hashlib.sha256(cp.read_bytes()).hexdigest()!=expected:continue
  if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()!=expected:continue
  for original,record in node.get('input_record_snapshots',{}).items():
   if original!=str(p.parent/'take.tsv'):continue
   ledger=pathlib.Path(record['snapshot'])
   if not ledger.is_file() or hashlib.sha256(ledger.read_bytes()).hexdigest()!=record['sha256']:continue
   for r in csv.DictReader(ledger.open(),delimiter='\t'):
    if r.get('n')==n:return {'source':r['source'],'licence':r.get('licence',''),'producer_record_snapshot':str(ledger),'producer_record_sha256':record['sha256'],'producer_csv_snapshot':str(cp),'producer_csv_sha256':expected}
 return None
