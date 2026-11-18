"""Rebuild independent staircase classes at a held target's exact fraction."""
import argparse,csv,json,math,os,pickle,sys,time
sys.path[:0]=['lane','.']
import modules as M
import zone_corner as Z
import twoshort_corner as T
from newclass import control
control()
n=int(sys.argv[1]);c1=int(sys.argv[2]);c2=int(sys.argv[3]);start=time.time()
H={int(r['n']):float(r['L']) for r in csv.DictReader(open('details.csv'))}
bar=json.load(open('bar.json')) if os.path.exists('bar.json') else {}
f=min(H[n],float(bar.get(str(n),H[n])))-math.isqrt(n-1)
out=f'plain/{n}-{c1}x{c2}';os.makedirs(out+'/runs',exist_ok=True);os.makedirs(out+'/zones',exist_ok=True)
limit=min(180.,float(open('search-deadline').read())-start-20)
print('START exact-f independent baseline',n,c1,c2,f,'limit',limit,flush=True)
a=argparse.Namespace(c1=c1,c2=c2,f=f,out=out+'/base.pkl',h='6,7,8,9,10',step=.2,per=2,top=9,walls=True,keep=0,seconds=limit,tag=f'sc25plain{n}')
T.cmd_stair(a)
if not os.path.exists(a.out):print('DONE no plain corners',n,flush=True);sys.exit()
Z.cmd_adopt([a.out,out+'/runs']);Z.cmd_table([out+'/runs',out+'/zones',out+'/zones.tsv','--all','--tag',f'sc25plain{n}-{c1}x{c2}'])
mods=pickle.load(open(out+'/zones/corners.pkl','rb'));mods=[q for q in mods if q['loss0']<=6.0];lens={}
for q in mods:q['ours']=True;lens[q['id']]=M.tabulate(q)
name=f'inbox/r25-priority-plain-{n}-{c1}x{c2}.pkl'
pickle.dump(dict(mods=mods,lens=lens,origin='new independent staircase at exact target fraction'),open(name+'.tmp','wb'));os.replace(name+'.tmp',name)
print('DONE plain',n,'arms',c1,c2,'f',f,'states',len(mods),'lowestloss',min((q['loss0'] for q in mods),default=None),'seconds',time.time()-start,flush=True)
