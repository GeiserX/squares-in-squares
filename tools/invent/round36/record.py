"""Write the round 36 results table from what exists in work/ (jobs.json, runs/*/done.json)."""
import json,csv,math,glob,os,sys,pathlib
S='$SCRATCH/bounties-squares/';W=S+'take-invent-r36/work/'
sys.path.insert(0,W+'tools');import heldshare as H
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S+'round36-briefs/bar36.tsv'),delimiter='\t')}
jobs={j['id']:j for j in json.load(open(W+'jobs.json'))}
out=sys.argv[1]
rows=[]
for d in sorted(glob.glob(W+'boxE/runs/*/done.json')):
 r=json.load(open(d));j=jobs.get(r['id'])
 if not j:continue
 n=j['n'];st=j['side']/math.sqrt(n)-1-bar[n]
 try:sh=H.share(W+'boxE/'+j['start'],n)[1][0]
 except Exception:sh=float('nan')
 rows.append(dict(job=r['id'],n=n,program=j['program'],seed=j['seed'],start=j['origin'].replace(S,''),start_sha256=j['input_sha256'][:16],held_share_1e3='%.3f'%sh,start_vs_bar36='%.3e'%st,end_vs_bar36=('%.3e'%(r['new']-bar[n])) if r.get('new') is not None else '',raw_finds=r.get('raw',''),search_end=r.get('search_end',''),error=r.get('error') or ''))
with open(out,'w',newline='') as h:
 w=csv.DictWriter(h,fieldnames=list(rows[0]),delimiter='\t');w.writeheader();w.writerows(rows)
print(len(rows),'rows')
