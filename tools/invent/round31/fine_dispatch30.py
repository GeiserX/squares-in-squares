"""Ensure the finer profile cannot enter a worker queue before its controls pass."""
import json,pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import controller28 as C
fixture=W/'fine-dispatch-control';fixture.mkdir(exist_ok=True)
marker=fixture/'FINE_ENTRY_GREEN';marker.unlink(missing_ok=True)
original=C.W;C.W=fixture
try:
 jobs=[dict(kind='fineentry',program='invent_barentry30c.py'),dict(kind='control',program='invent_barentry30c.py')]
 path=fixture/'queue-fine.json';C.atomic(path,jobs)
 assert json.load(open(path))==[jobs[1]]
 marker.write_text('fixture control passed')
 C.atomic(path,jobs);assert json.load(open(path))==jobs
finally:C.W=original
(W/'fine-dispatch-controls.json').write_text(json.dumps(dict(unproved_production_blocked=True,controls_preserved=True,proved_production_admitted=True)))
print('CONTROL unproved finer production blocked; numerical controls preserved; proved finer production admitted')
