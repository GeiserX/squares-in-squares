"""Recognize a held boundary without using numeric similarity on owned layouts."""
import re

def boundary(proof):
 for key,node in proof.get('nodes',{}).items():
  source=node.get('source','');record=node.get('record','')
  if re.search(r'(?:^|/)results/round\d+-best-[^/\s]+\.tsv(?: n=\d+)?$',record):return dict(node=key,kind='held source ledger',record=record)
  if re.search(r'held(?: packing)?(?: of)? n\s*=\s*\d+(?: of round \d+)?|held round\s*\d+b? n\s*=?\s*\d+|n\s*=\s*\d+ (?:from|of) held round\s*\d+',source,re.I):return dict(node=key,kind='held reference',source=source[:500])
  if re.search(r'(?:$SCRATCH/bounties-squares/)?gather/round\d+-2026-\d\d-\d\d[a-z]?\.csv',source):return dict(node=key,kind='gathered held row',source=source[:500])
 return None

def controls():
 assert boundary(dict(nodes={'r':dict(source='own follow of held n = 416 of round 28',record='input.csv')}))
 assert boundary(dict(nodes={'r':dict(source='public supplier/test :: old file',record='/repo/lanes/squares/results/round28-best-2026-11-15.tsv n=416')}))
 assert not boundary(dict(nodes={'r':dict(source='public supplier/test :: fetched file',record='/scratch/public416.csv')}))
 assert not boundary(dict(nodes={'r':dict(source='public supplier/test :: comparison mentions results/round28-best-2026-11-15.tsv',record='/scratch/public416.csv')}))
 print('CONTROL held references and producer ledgers are owned; fetched public rows and comparison citations remain public',flush=True)

if __name__=='__main__':controls()
