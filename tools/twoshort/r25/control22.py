import pathlib,pickle,subprocess,sys
R=pathlib.Path.home()/'scratch/squares-twoshort';sys.path.insert(0,str(R/'lane'));import zone_corner as Z
D=R/'design-control';D.mkdir(exist_ok=True)
with open(D/'run.log','w') as log:
 subprocess.run([sys.executable,'-I',str(R/'lane/twoshort_corner.py'),'stair','8','8','.713437',str(D/'base.pkl'),'--top','0','--seconds','120','--tag','ctl22'],stdout=log,stderr=subprocess.STDOUT,check=True)
base=pickle.load(open(D/'base.pkl','rb'));loss=min(Z.loss_of(Z.cmod(8,8),q['f'],q['count'],q['y0'],q['x0']) for q in base)
s='staircase 8x8 f=.713437 min_loss='+repr(loss)+' count='+str(len(base));print(s,flush=True)
assert 2.466<loss<2.469,s
(R/'CONTROL-PASS').write_text(s+'\n')
