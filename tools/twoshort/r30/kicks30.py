"""Print every finished kick of round 29 with its gap to the bar side (local mirror)."""
import json,glob,sys
W='$SCRATCH/bounties-squares/take-twoshort-r30/work'
bar=json.load(open(W+'/bar.json'));rows=[]
for p in glob.glob(W+'/boxE30/done/*.json'):
 d=json.load(open(p))
 if 'start_side' not in d or d.get('tag','').startswith('control'):continue
 b=bar[str(d['n'])];rows.append((d['best']-b,d['n'],d['tag'],d['seed'],d['tries'],d['start_side']-d['best'],d.get('seconds',180),d.get('ab','')))
rows.sort()
for r in rows[:int(sys.argv[1]) if len(sys.argv)>1 else 40]:print('gap %+.3e n=%d %s s%d tries %d moved %.3e sec %s %s'%r)
print('kicks',len(rows),'moved',sum(r[5]>1e-8 for r in rows),'below bar',sum(r[0]<0 for r in rows))
