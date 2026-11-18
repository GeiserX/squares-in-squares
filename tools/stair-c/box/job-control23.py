import importlib.util,json,os,pickle,sys
sys.path.insert(0,'lane');import modules as M
spec=importlib.util.spec_from_file_location('stair_job','lane/stair-c_job.py');J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
L=pickle.load(open('libbase/library.pkl','rb'));l=next(x for x in L['layouts'] if x['n']==975 and x['tag']=='tw17');F1,F2,C=l['ids_slide']
args=['libbase','job-control-raw','details-r21.csv','975-early-control','975',C,F1,F2,str(l['s1']),str(l['s2']),repr(l['f']+.0001),'--fq','./fq','--squeeze','family']
J.run(args)
a=json.load(open('job-control-raw/975-early-control-slp.json'));b=json.load(open('job-control-raw/975-early-control.json'))
for stem in ['975-early-control-slp','975-early-control']:
 P=M.np.asarray(M.read_layouts('job-control-raw/'+stem+'.csv')[975],float);s,g=M.layout_state(P);assert len(P)==975 and g>=-1e-7 and s<l['s']+1e-5
assert a['early_stage'] and a['built']>=b['built']-1e-7
open('EARLY_JOB_READY','w').write(str(b['built']))
print('CONTROL early job975 legal early/final sides',a['built'],b['built'],'reference',l['s'],'certified-file quench still separate',flush=True)
