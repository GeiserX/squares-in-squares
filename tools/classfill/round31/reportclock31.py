"""Guarantee the first report write at 00:25 UTC even if final cleanup is slow."""
import time,os,json,csv,math,sys
from pathlib import Path
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent
end=float((W/'stage/deadline').read_text())+600
while time.time()<end-2:time.sleep(min(30,end-2-time.time()))
p=W/'report-final.json'
if p.exists():data=p.read_bytes()
else:
 csv.field_size_limit(100000000)
 take=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));base={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round31-briefs/bar31.tsv'),delimiter='\t')};live=dict(base)
 for f in S.glob('take-*-r31/take.tsv'):
  if f.parent==T:continue
  for r in csv.DictReader(open(f),delimiter='\t'):
   try:n=int(r['n']);live[n]=min(live[n],float(r['new']))
   except:pass
 kept=[r for r in take if float(r['new'])<live[int(r['n'])]-1e-10]
 def read(f,d):
  try:return json.loads(f.read_text())
  except:return d
 git=read(W/'git-receipt.json',{});measure=read(W/'measurements.json',{})
 r=dict(lane='classfill',improved_n=len(kept),gain=dict(against_base_bar=sum(base[int(r['n'])]-float(r['new']) for r in kept),beyond_other_live_r31=sum(live[int(r['n'])]-float(r['new']) for r in kept)),take_dir=str(T),summary='Deadline snapshot of certified classfill rows. Final cleanup or report preparation did not finish before the report clock.',what_was_measured=[json.dumps(measure,sort_keys=True)],next=['Use the immutable work/ receipts to continue changed endpoint searches.'],commits=git.get('commits',[]),processes_left=['consult archive-verification.json and STATE.txt'],blocked=['deadline report preparation incomplete'],repo='$PRIVATE_REPO',branch='main',worktree='$PRIVATE_REPO',pr='none (direct main commit)')
 data=(json.dumps(r,indent=2)+'\n').encode()
tmp=W/'reportclock-final.json';tmp.write_bytes(data)
while time.time()<end:time.sleep(min(.05,end-time.time()))
os.replace(tmp,T/'report.json')
