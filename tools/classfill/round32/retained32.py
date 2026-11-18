"""Audit retained bytes, completed quench receipts and the pinned input tree."""
import sys,math
from pathlib import Path
W=Path(__file__).parent;sys.path.insert(0,str(W));import run32 as C
from lineage32 import attach,tree

def audit(path,receipt):
 path=Path(path);receipt=Path(receipt);r=C.read(receipt);n=r['job']['n'];digest=C.sha(path);score=r['score']
 assert digest==r['output_sha256'],'retained bytes differ from receipt'
 numerical=r['finish']['original_byte_audit'];q=r['quench_receipt']
 assert numerical['passed'] and numerical['input_sha256']==digest,'original-byte audit does not bind retained bytes'
 assert numerical['direct']=='ok' and numerical['pandas']=='ok','one metric read failed'
 assert abs(numerical['direct_score']-score)<1e-14 and abs(numerical['pandas_score']-score)<1e-14,'metric score differs'
 assert r['finish']['finish_quenched'] and q['completed']>0 and q['output_sha256']==digest,'certified-file quench does not bind retained bytes'
 assert abs(q['after_score']-score)<1e-14,'quench score differs'
 assert C.proof_clear(receipt)[0],'withdrawn source in current input tree'
 binding=attach(path,receipt)
 from source32 import F
 clean,proof=F.queue_source_check(path,n,C.S,seconds=30)
 result=dict(time=C.now(),path=str(path),n=n,sha256=digest,score=score,numerical=numerical,quench=q,source_clean=clean,source_proof=proof,primary_binding=binding,receipt=str(receipt),receipt_sha256=C.sha(receipt))
 C.atom(W/'retained-audits'/f'{n}-{digest}.json',result)
 assert clean,'independent source audit refused retained bytes'
 assert C.sha(path)==digest,'retained bytes changed during audit'
 return result

def all_retained():
 records={}
 for row in C.rows(C.T/'take.tsv'):
  n=int(row['n']);path=C.T/f'{n}.csv';meta=C.read(path.with_suffix('.source.json'));result=audit(path,meta['receipt']);records[str(n)]={k:result[k] for k in ('sha256','score','source_clean','primary_binding','receipt')}
 C.atom(W/'retained-verification.json',dict(time=C.now(),records=records))
 C.note('RETAINED_AUDIT_PASS '+str(len(records))+' rows; exact bytes, both metric reads, completed certified-file fq, independent primary source walk')
 return records

if __name__=='__main__':
 all_retained();print('RETAINED_AUDIT_PASS',flush=True)
