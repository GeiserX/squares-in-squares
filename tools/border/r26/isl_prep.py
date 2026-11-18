"""isl_prep.py RAW.csv N OUT.start.txt   render an island result as an fq start file (boxA, light)
   isl_prep.py --back N BEST.txt OUT.csv  turn the best fq packing of the chain back into a csv."""
import sys,math,csv
from pathlib import Path
W=Path(__file__).parent
src=(W/'driver.py').read_text();src=src[:src.index("log('start round26 collector/scanner")]
src=src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_islprep','__file__':str(W/'driver.py')};exec(compile(src,str(W/'driver.py'),'exec'),ns)
bs=ns['bs']
if sys.argv[1]=='--back':
 n=int(sys.argv[2]);_,A=bs.read_txt(sys.argv[3])
 with open(sys.argv[4],'w') as f:
  w=csv.writer(f);w.writerow(['n','square_id','x','y','angle'])
  for i,(x,y,a) in enumerate(A):w.writerow([n,i,repr(x),repr(y),repr(math.radians(a))])
else:
 n=int(sys.argv[2]);rows=[r for r in csv.DictReader(open(sys.argv[1])) if int(r['n'])==n]
 s,A=bs.normalize([(float(r['x']),float(r['y']),float(r['angle'])) for r in rows])
 bs.write_txt(sys.argv[3],s+1e-10,A);print('start',sys.argv[3],'side',s)
