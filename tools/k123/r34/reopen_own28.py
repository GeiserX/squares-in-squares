"""Add targeted own share-only parked endpoints without scanning every frozen near file."""
from pathlib import Path
import time,re,json
W=Path(__file__).resolve().parent;S=W.parent.parent;paths=[]
for lane,ns in [('invent',{910}),('forensics',{599,647,699,860}),('k123',{699,798,932})]:
 root=S/f'take-{lane}-r27'
 paths += [str(p) for p in (root/'near').glob('*.csv') if re.match(r'(?:'+ '|'.join(map(str,ns))+r')[-.]',p.name)]
 for directory in (root/'work').iterdir():
  if not directory.is_dir() or not re.search(r'withdr|held|exclu|share|quarant',directory.name,re.I):continue
  paths += [str(p) for p in directory.rglob('*.csv') if re.match(r'(?:'+ '|'.join(map(str,ns))+r')[-.]',p.name)]
marker=W/'reopened-inputs27.txt';old=marker.read_text().splitlines();marker.write_text('\n'.join(dict.fromkeys(paths+old))+'\n')
(W/'reopened-targeted28.json').write_text(json.dumps(paths,indent=2))
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA REOPEN {len(paths)} targeted frozen own share-only endpoints: invent910,forensics599/647/699/860,k123699/798/932. Original files remain read-only; direct starts still require complete source admission and new byte snapshots. List work/reopened-targeted28.json. Deadline07:25Z.\n')
print('targeted candidates',len(paths),flush=True)
