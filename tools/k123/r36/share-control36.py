from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from publicshare31 import policy
m=policy();paths=m.archive_paths();expected=json.load(open(W/'share/zips.json'));assert len(paths)==10 and [str(p) for p in paths]==[p for p,h in expected]
result={'frozen_versions':len(paths),'all_sha256_match':all(hashlib.sha256(p.read_bytes()).hexdigest()==h for p,(_,h) in zip(paths,expected)),'share_measure':'frozen share31','tolerances':m._assembler.TOLS};assert result['all_sha256_match'];(W/'share-control36.json').write_text(json.dumps(result));print(json.dumps(result))
