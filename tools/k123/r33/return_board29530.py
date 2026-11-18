from pathlib import Path
import sys,json,hashlib,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')]
from stage24 import stage,mlp
control=json.load((W/'board-selector-control30.json').open());assert control['added_target_starts']>0 and 295 in control['targets']
paths={295:W.parent/'295.csv',367:Path(json.load((W/'return36730.json').open())['path'])};P={n:mlp.load(str(p),{n})[n] for n,p in paths.items()};orig={n:str(p) for n,p in paths.items()};tag='freshreturnboard29530';assert stage(tag,P,orig,[(295,367)],'fresh-board-return','certified295 with changed return367 at19.688956051052; allow candidate295 despite the older board filter; all certification bars unchanged',board_targets=[295])
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START controlled295 self-follow with changed367 donor56c1352a31b4a554, allowing295 proposals despite old-board cutoff. Positive selector control retained every baseline start and added295 starts. Floatsafe, bar30/live thresholds and all source gates unchanged. Log out/scanfreshreturnboard29530.log; deadline00:15Z.\n')
