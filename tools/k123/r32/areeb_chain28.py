"""Carry relevant areebbb root notices into both published ledger cells."""
import pathlib,re,json,csv
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent
PUBLIC=S/'take-harvest-r22/work/public/data/nb'
PATH=re.compile(r'$DATA/[^\s,;<>"\\]+\.json')
HARVEST=re.compile(r'($SCRATCH/bounties-squares/take-harvest-r[0-9]+)/([0-9]+)\.csv')
LEDGERS={}
REMOTE=re.compile(r'$DATA/[^\s,;<>"\\]+/remote-[0-9a-f]+\.json')
def strings(obj):
 if isinstance(obj,dict):
  for value in obj.values():yield from strings(value)
 elif isinstance(obj,list):
  for value in obj:yield from strings(value)
 elif isinstance(obj,str):yield obj
def roots(row):
 queue=[row];seen=set();ns=set()
 while queue:
  obj=queue.pop()
  for text in strings(obj):
   for directory,number in HARVEST.findall(text):
    if directory not in LEDGERS:
     ledger=pathlib.Path(directory)/'take.tsv'
     LEDGERS[directory]={r['n']:r for r in csv.DictReader(ledger.open(),delimiter='\t')} if ledger.exists() else {}
    record=LEDGERS[directory].get(number,{})
    if 'areebbb/' in record.get('source',''):ns.add(int(number))
   if 'areebbb/' in text:
    for match in re.finditer('areebbb/',text):
     chunk=text[match.start():match.start()+800]
     q=REMOTE.search(chunk)
     if q and pathlib.Path(q[0]).exists():
      proof=json.loads(pathlib.Path(q[0]).read_text())
      if 'input_hash' in proof and 'n' in proof:ns.add(int(proof['n']))
   for name in PATH.findall(text):
    if name in seen:continue
    seen.add(name);p=pathlib.Path(name)
    if p.exists():
     try:queue.append(json.loads(p.read_text()))
     except (ValueError,OSError):pass
 return sorted(ns)
def enrich(path,row):
 row=dict(row);ns=roots(row)
 if not ns:return row
 table={int(z['n']):z for z in csv.DictReader((PUBLIC/'areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv').open())}
 atlas={int(z['n']):z for z in csv.DictReader((PUBLIC/'malyshevdanil__squares-in-squares-living-atlas-of-tight-packings/submission_sources.csv').open())}
 for n in ns:
  z=table[n];label=f'areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n = {n}'
  if label in row['source'] and label in row.get('licence',''):continue
  source=label+': '+json.dumps(z,separators=(',',':'));licence=label+', Apache 2.0 (Kaggle default for public notebooks)'
  if 'malyshevdanil/' in z['src']:
   a=atlas[n];assert a['source'].startswith('sub:'),(n,a)
   source+=' -> malyshevdanil/squares-in-squares-living-atlas-of-tight-packings :: submission_sources.csv: '+json.dumps(a,separators=(',',':'))
   licence+=' -> malyshevdanil/squares-in-squares-living-atlas-of-tight-packings :: '+a['source'][4:]+f' (submission_sources.csv donor n = {n}), Apache 2.0 (Kaggle default for public notebooks)'
  else:
   # Other upstream families need their existing table or explicit source-specific chain.
   raise ValueError('areebbb root needs explicit upstream chain: '+str((n,z)))
  row['source']+=' | '+source;row['licence']=row.get('licence','')+' | '+licence
 return row
