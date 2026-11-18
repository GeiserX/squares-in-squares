"""List frozen r22-r26 take and near csv files (and the re-opened seed split) whose raw side is below the bar27 side."""
import csv,glob,math,json,os,sys
S='$SCRATCH/bounties-squares'
L={int(r['n']):(float(r['score'])+1)*math.sqrt(int(r['n'])) for r in csv.DictReader(open(S+'/take-border-r27/work/bar27-details.csv'))}
files=[]
for rnd in ('r26','r25','r24','r23','r22'):
 for t in glob.glob(f'{S}/take-*-{rnd}'):
  files+=[p for p in glob.glob(t+'/[0-9]*.csv')]+glob.glob(t+'/near/*.csv')+glob.glob(t+'/work/withdrawn/*.csv')+glob.glob(t+'/work/*/withdrawn/*.csv')
files+=glob.glob(S+'/take-border-r27/work/seedsplit/*/*.csv')
out=[]
for p in files:
 try:
  if os.path.getsize(p)>1500000:continue
  xs=[];n=None
  for r in csv.DictReader(open(p)):
   n=int(r['n']);a=float(r['angle']);h=.5*(abs(math.cos(a))+abs(math.sin(a)));xs.append((float(r['x']),float(r['y']),h))
  if n is None or len(xs)!=n or n not in L:continue
  s=max(max(x+h for x,y,h in xs)-min(x-h for x,y,h in xs),max(y+h for x,y,h in xs)-min(y-h for x,y,h in xs))
  g=s-L[n]
  if g<1e-8:out.append((g,n,p))
 except Exception as e:continue
out.sort()
for g,n,p in out:print(f'{g:.3e}\t{n}\t{p}')
print(len(files),'files',file=sys.stderr)
