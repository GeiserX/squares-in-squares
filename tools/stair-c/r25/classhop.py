"""Give new independent core-step geometry one bounded deletion and hop pass."""
import os,pickle,sys,time
sys.path.insert(0,'lane')
import modules as M
import zone_corner as Z
n=int(sys.argv[1]);a=pickle.load(open(f'inbox/r25-priority-class-{n}.pkl','rb'));q=min(a['mods'],key=lambda q:q['loss0'])
# Every input here came from the controlled core-step constructor in this run.
assert 'independent staircase with equal-area core-step transfer' in q['src']
assert q['licence']=='our own'
mod=Z.cmod(q['c1'],q['c2'],q['lean1'],q['lean2']);g=Z.exact(q['P'],mod,q['f0'],q['y0']+1e-7,q['x0']+1e-7)
assert min(g[:3])>=-1e-7 and g[3]==0
bad=Z.exact(M.np.vstack([q['P'],q['P'][0]]),mod,q['f0'],q['y0']+.001,q['x0']+.001)
assert min(bad[:3])<-.99
print('CONTROL class-hop exact source passes; duplicate rejected; n',n,'start loss',q['loss0'],flush=True)
b=dict(id=q['id'],src=q['src'],licence=q['licence'],c1=q['c1'],c2=q['c2'],lean1=q['lean1'],lean2=q['lean2'],count=q['count'],P=q['P'],f=q['f0'],y0=q['y0'],x0=q['x0'])
out=f'classhop/{n}';os.makedirs(out+'/runs',exist_ok=True);os.makedirs(out+'/zones',exist_ok=True)
pickle.dump([b],open(out+'/base.pkl','wb'))
Z.cmd_search([out+'/base.pkl',out+'/runs','--moves','self,delete,hop','--down','2','--beam','2','--minutes','3','--slot','30','--tail','10','--no-trade','--deadline','search-deadline','--seed','25'])
Z.cmd_table([out+'/runs',out+'/zones',out+'/zones.tsv','--all','--tag',f'sc25hop{n}'])
mods=pickle.load(open(out+'/zones/corners.pkl','rb'));lens={}
for v in mods:v['ours']=True;lens[v['id']]=M.tabulate(v)
pickle.dump(dict(mods=mods,lens=lens,origin='independent core-step deletion and hop'),open(f'inbox/r25-priority-classhop-{n}.pkl.tmp','wb'));os.replace(f'inbox/r25-priority-classhop-{n}.pkl.tmp',f'inbox/r25-priority-classhop-{n}.pkl')
print('DONE class-hop',n,'states',len(mods),'lowestloss',min((v['loss0'] for v in mods),default=None),flush=True)
