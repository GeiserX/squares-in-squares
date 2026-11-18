"""Carry areebbb's actual per-count upstream chain into both table cells."""
from common28 import *
def credit(proof):
 a=read(proof,{})
 history=a.get('expanded',{}).get('history',{})
 parts=sorted(set(s for s in history.get('parts',[]) if s.startswith('areebbb per_n.csv donor n = ')))
 licences=sorted(set(s for s in history.get('licences',[]) if 'areebbb/' in s and 'per_n.csv' in s))
 other=sorted(set(s for s in history.get('licences',[]) if s.startswith('kmmmvs/') and 'Other' in s))
 return '; '.join(parts+other),'; '.join(licences+other)
def attach(record,proof):
 source,licence=credit(proof)
 if source and source not in record.get('source',''):record['source']+='; upstream per_n chain: '+source
 if licence and licence not in record.get('licence',''):record['licence']+='; upstream per_n notices: '+licence
 return record
if __name__=='__main__':
 for p in (W/'audited').glob('*.json'):
  a=read(p,{})
  if a.get('accepted') and a.get('input_proof'):atomic(p,attach(a,a['input_proof']))
 print('CREDITS_AUDITS_UPDATED')
