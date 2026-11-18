from pathlib import Path
import sys,json,csv,tempfile,hashlib
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from publish_certified36 import publish
state=json.load(open(W/'near-state36.json'));key,j=next((k,j) for k,j in state.items() if j.get('path','').endswith('972-join36-8021b4ff4dd1d926.csv'));D=W/'near-cert36'/key;p=D/'972.csv';result=json.load(open(D/'result36.json'));meta=json.load(open(j['path']+'.json'));proof=json.load(open(D/'source-walk26.json'));bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(W.parent.parent/'round36-briefs/bar36.tsv'),delimiter='\t')}
root=W/'publication-controls36';root.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=root) as tmp:
 S=Path(tmp);T=S/'take-k123-r36';C=T/'work';C.mkdir(parents=True)
 r=publish(972,p,meta,result,proof,key,bar[972],work=C,do_register=False);assert r and (T/'972.csv').read_bytes()==p.read_bytes()
 assert publish(972,p,meta,result,proof,key,bar[972],work=C,do_register=False) is None
 (T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');peer=S/'take-peer-r36';peer.mkdir()
 (peer/'take.tsv').write_text('n\tnew\n972\t'+repr(result['score']-2e-6)+'\n')
 assert publish(972,p,meta,result,proof,key,bar[972],work=C,do_register=False) is None
 r={'real_full_fq_layout_published_to_isolated_take':True,'csv_bytes_unchanged':True,'duplicate_rejected':True,'lower_live_peer_rejected':True,'input_n':972,'csv_sha256':hashlib.sha256(p.read_bytes()).hexdigest()};(W/'publication-control36.json').write_text(json.dumps(r));print(json.dumps(r))
