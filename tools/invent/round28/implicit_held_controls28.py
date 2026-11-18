"""Resolve implicit held references only from their exact versioned published row."""
import pathlib,json,sys
W=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r28/work');sys.path.insert(0,str(W))
import ancestry28 as A
path=A.R/'results/round10-best-2026-11-11.tsv';row=A.source_table(str(path),path.stat().st_mtime_ns)[756];record=str(path)+' n=756'
assert row['source']=='fq quench of the held packing (own soft-box search, methods_soft.py)'
assert A.implicit_held(row['source'],record)==('756','9')
assert A.previous_round(record)==9
assert A.previous_round(str(A.R/'results/round9-best-2026-11-11.tsv')+' n=756')==8
assert A.implicit_held(row['source']+' changed',record)is None
assert A.implicit_held(row['source'],str(path)+' n=757')is None
assert A.implicit_held(row['source'],str(W/'invented-round10-best.tsv')+' n=756')is None
result=dict(actual_round10_756_refers_to_round9=True,round9_refers_to_round8=True,changed_source_refused=True,wrong_row_refused=True,nonpublished_record_refused=True)
(W/'implicit-held-controls.json').write_text(json.dumps(result));print(json.dumps(result))
