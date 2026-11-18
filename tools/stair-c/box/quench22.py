import csv,json,os,sys
sys.path.insert(0,'lane')
import family_step as fs
p=sys.argv[1]; out=sys.argv[2]; n=int(os.path.basename(p).split('-')[0])
L,X=fs.canon(fs.load(p)[n]); s,Y=fs.fq_quench(L,X,(),timeout=240)
if s is not None and s<L: X=Y
fs.write_rows(out,n,X)
j=json.load(open(p[:-4]+'.json')); j['certified_file_quench']={'start':L,'end':s};json.dump(j,open(out[:-4]+'.json','w'))
print(n,'certified file quench',L,s,flush=True)
