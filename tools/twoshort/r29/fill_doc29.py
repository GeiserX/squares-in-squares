"""Fill the round 29 doc section (doc/s18.md) with the final take numbers and the kick counts."""
import json,subprocess,sys
from pathlib import Path
W=Path(__file__).parent;PY=str(W.parent.parent/'venv/bin/python')
f=json.loads(subprocess.run([PY,'-I',str(W/'final29.py')],capture_output=True,text=True).stdout)
st=subprocess.run([PY,'-I',str(W/'stats29.py')],capture_output=True,text=True).stdout.strip().split('\n\n')
INPUT={504:('the backlog take row of 08:41','one 900 s midm kick'),737:('a forensics rectangle','a 180 s lkick'),752:('the backlog take row of 09:24','the second 900 s midm leg')}
rows='\n'.join('| %d | %.3e | %.3e | %s | %s |'%(r['n'],r['gain'],r['beyond'],*INPUT.get(r['n'],('?','?'))) for r in sorted(f['rows'],key=lambda r:r['n']))
s=(W/'doc/s18.md').read_text()
tools='Round 29 ran %s kicks in total.\nBy tool the kicks moved as follows:\n\n%s\n\nBy input lane:\n\n%s'%(st[0].split('\n')[2].split('|')[2].strip(),st[1].replace('| tool |','| tool |'),st[2])
s=s.replace('@@NROWS@@',str(len(f['rows']))).replace('@@GAIN@@','%.3e'%f['gain']).replace('@@ROWS@@',rows).replace('@@TOOLS@@',tools)
(W/'doc/s18-final.md').write_text(s);print(s[:1500])
