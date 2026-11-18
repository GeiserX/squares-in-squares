"""Create missing follow directories and resume exactly the same certified input."""
import copy,importlib.util,json,pathlib,sys,tempfile
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H))
s=importlib.util.spec_from_file_location('follow_stage_control',H/'follow-near.py');F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
rows=[dict(n='1',square_id='0',x='0.5',y='0.5',angle='0')];meta=dict(n=1,source_sha256='known-control-bytes')
with tempfile.TemporaryDirectory(prefix='stair-c-follow-')as folder:
    target=pathlib.Path(folder)/'missing/cert-in/1-control.csv'
    try:F.C.write(str(target),rows)
    except FileNotFoundError:pass
    else:raise AssertionError('missing-directory failure was not reproduced')
    assert F.stage_target(target,rows,meta)is False and target.exists()
    assert F.stage_target(target,rows,meta)is True
    for changed_rows,changed_meta in[(rows,dict(meta,source_sha256='changed')) ,([dict(rows[0],x='1.5')],meta)]:
        try:F.stage_target(target,changed_rows,changed_meta)
        except AssertionError:pass
        else:raise AssertionError('changed input reused an existing target')
print('CONTROL follow stage: old missing-parent failure reproduced; parent created; exact input resumed; changed hash and coordinates refused')
