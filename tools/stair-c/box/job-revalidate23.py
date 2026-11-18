import json,pickle,sys
sys.path.insert(0,'lane');import modules as M
L=pickle.load(open('libbase/library.pkl','rb'));l=next(x for x in L['layouts'] if x['n']==975 and x['tag']=='tw17')
for stem in ['975-early-control-slp','975-early-control']:
 P=M.np.asarray(M.read_layouts('job-control-raw/'+stem+'.csv')[975],float);s,g=M.layout_state(P)
 print('CONTROL early job roundtrip',stem,'count',len(P),'side',s,'gap',g,'reference',l['s'],flush=True)
 assert len(P)==975 and g>=-1e-7 and s<l['s']+1e-5
open('EARLY_JOB_READY','w').write(str(s))
print('CONTROL early/final CSV roundtrip PASS; radians kept unchanged; early export enabled',flush=True)
