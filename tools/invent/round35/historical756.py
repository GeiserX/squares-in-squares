"""Resolve the exact round 8 n756 polish omitted by the generic held reader."""
import csv,hashlib,json,pathlib
S=pathlib.Path('$SCRATCH/bounties-squares')
R=pathlib.Path('results')
W=pathlib.Path(__file__).resolve().parent

def rows(path, delimiter=','):
 return list(csv.DictReader(open(path),delimiter=delimiter))

def resolve(n,rnd,manifest=None):
 if (int(n),int(rnd))!=(756,8):return None
 m=manifest or json.load(open(W/'historical756-proof.json'))
 try:
  for pin in m['pins']:
   if hashlib.sha256(pathlib.Path(pin['path']).read_bytes()).hexdigest()!=pin['sha256']:return None
  packing=rows(S/'take-polish-r7/756.csv')
  old=next(r for r in rows(S/'take-polish-r7/take.tsv','\t')if r['n']=='756')
  root=next(r for r in rows(R/'harvest-best-2026-11-11.tsv','\t')if r['n']=='756')
  gate=next(r for r in rows(S/'gate/cand-round8-1111a/details.csv')if r['n']=='756')
  if old!=m['polish_row']or root!=m['public_row']or gate!=m['gate_row']:return None
  if len(packing)!=756 or any(r['n']!='756'for r in packing):return None
  if float(old['held'])!=float(root['score'])or float(old['new'])!=float(gate['score']):return None
  # The gathered round8 n756 and saved polish n756 matched every numeric coordinate exactly.
  if m['gathered_numeric_sha256']!=m['packing_numeric_sha256']:return None
  numeric=json.dumps([[float(r[k])for k in('x','y','angle')]for r in packing],separators=(',',':')).encode()
  if hashlib.sha256(numeric).hexdigest()!=m['packing_numeric_sha256']:return None
 except (OSError,KeyError,ValueError,StopIteration):return None
 source='own fq polish r7, exact retained n756 at round8, upstream '+root['source']+'; original public ledger '+str(R/'harvest-best-2026-11-11.tsv')+' n=756; immutable historical proof '+str(W/'historical756-proof.json')
 return dict(n='756',score=old['new'],source=source,licence=root['licence']),str(W/'historical756-proof.json')
