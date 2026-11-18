from pathlib import Path
import tempfile,tarfile,io,hashlib,json,sys,time
W=Path(__file__).resolve().parent;src=(W/'boxCD_import33.py').read_text()
with tempfile.TemporaryDirectory(dir=W) as d:
 R=Path(d);(R/'claims').mkdir();(R/'queue.tsv').write_text('old queue')
 files={'queue.tsv':b'new queue','bars.tsv':b'bars','boxD-pools33.json':b'["fresh-control"]','boxD-claims33.json':b'[]','fresh-control.csv':b'packing','sources-fresh-control.json':b'{}','bars-fresh-control.tsv':b'bars'}
 def bundle(files):
  p=R/'boxCD-export33.tgz'
  with tarfile.open(p,'w:gz') as t:
   for name,data in files.items():
    m=tarfile.TarInfo(name);m.size=len(data);t.addfile(m,io.BytesIO(data))
  return hashlib.sha256(p.read_bytes()).hexdigest()
 def execute(digest):
  old=sys.argv;sys.argv=['import-control',digest]
  try:exec(compile(src.replace("R=Path.home()/'scratch/squares-k123'",f'R=Path({str(R)!r})'),'boxCD_import33.py','exec'),{})
  finally:sys.argv=old
 execute(bundle(files));assert (R/'queue.tsv').read_text()=='new queue';assert (R/'fresh-control.csv').read_bytes()==b'packing'
 files['fresh-control.csv']=b'tampered';files['queue.tsv']=b'bad queue'
 try:execute(bundle(files))
 except AssertionError:pass
 else:raise AssertionError('changed immutable input accepted')
 assert (R/'queue.tsv').read_text()=='new queue' and (R/'fresh-control.csv').read_bytes()==b'packing'
result={'complete_bundle_published':True,'changed_immutable_input_rejected':True,'failed_bundle_preserved_prior_queue':True}
(W/'import-control34.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA FINISH atomic import control: complete bundle accepted; changed immutable file rejected before queue publication; prior queue and packing unchanged on failure. work/import-control34.json.\n')
