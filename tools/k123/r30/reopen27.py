"""Feed previously refused source designs before saved unchanged recipes."""
import pathlib,json,re,time,csv,shutil
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent
marker=W/'reopened-inputs27.txt'
if marker.exists():raise SystemExit
from provenance24 import mlp,credit
from policy27 import lifted
D=W/'reopened';D.mkdir(exist_ok=True);paths=[]
# Preserve withdrawn certificates with their original source row.
for n in [932,922]:
 src=S/f'take-k123-r26/work/withdrawn/{n}.csv';jp=src.with_name(f'{n}-source-withdrawn26.json')
 if src.exists() and jp.exists():
  dest=D/f'{n}-reopened-r26.csv';shutil.copy(src,dest);pathlib.Path(str(dest)+'.json').write_bytes(jp.read_bytes());paths.append(str(dest))
paths.append(str(S/'take-k123-r25/982.csv'))
# Round26 source-refused queue includes permitted Samanyu ancestry. Retest rather than use labels.
state=(S/'take-k123-r26/STATE.txt').read_text()
paths+=re.findall(r'DROP source-refused fresh input (\S+\.csv)',state)
for lane in ['forensics','stair-c','modules','twoshort','midm','invent','rebuild','harvest']:
 for rnd in [26]:
  root=S/f'take-{lane}-r{rnd}'
  paths+=map(str,root.glob('*.csv'));paths+=map(str,(root/'near').glob('*.csv'))
# Known roots and the lifted 23a source families are available through their source tables.
for rnd in [24,25]:
 root=S/f'take-k123-r{rnd}'
 for n in [228,365,415,501,503,534,735,790,809,866,921,927,932,968,982,990]:
  p=root/f'{n}.csv'
  if p.exists():paths.append(str(p))
paths=list(dict.fromkeys(p for p in paths if pathlib.Path(p).exists()))
marker.write_text('\n'.join(paths)+'\n')
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA REOPEN {len(paths)} historical candidates for source recheck, priority932/922/982 then formerly refused r26 inputs. Missing-parent and remaining excluded trees still fail. Logs work/stage24.py.log; deadline17:45Z.\n')
print('reopen candidates',len(paths),flush=True)
