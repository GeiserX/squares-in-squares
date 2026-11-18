"""Recover an exact retired public row from its captured ledger and input receipt."""
import csv,hashlib,json,pathlib
S=pathlib.Path('$SCRATCH/bounties-squares')
KNOWN={str(S/'take-harvest-r27/793.csv'):S/'take-classfill-r27/work/ancestry/9f87f0f65f1d0079e409bcf0e3df673f9c023da9ffd88e9439fce01da36bd211.json'}
def valid_pin(pin):
 try:return hashlib.sha256(pathlib.Path(pin['snapshot']).read_bytes()).hexdigest()==pin['sha256']
 except (OSError,KeyError):return False

def metadata(path,n):
 proof=KNOWN.get(str(path))
 if proof is None:return '','',''
 try:
  value=json.load(open(proof))
  if value['input']!=str(path)or value['n']!=n:return '','',''
  pins=value['snapshots'];packing=next(v for v in pins if v['sha256']==value['input_sha256'])
  ledger=next(v for v in pins if v['path']==str(pathlib.Path(path).parent/'take.tsv'))
  if not valid_pin(packing)or not valid_pin(ledger):return '','',''
  rows=list(csv.DictReader(open(packing['snapshot'])))
  if len(rows)!=n or any(int(v['n'])!=n for v in rows):return '','',''
  row=next(v for v in csv.DictReader(open(ledger['snapshot']),delimiter='\t')if int(v['n'])==n)
  if row['source']!=value['source']or row['licence']!=value['licence']:return '','',''
  source=row['source']+'; exact archived public row proof '+str(proof)+'; certified input '+packing['snapshot']+' sha256 '+packing['sha256']
  return source,row['licence'],str(proof)
 except (OSError,ValueError,KeyError,StopIteration):return '','',''
