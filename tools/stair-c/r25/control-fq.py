"""Positive control for a real fq invocation on an independent certified 975."""
import csv,json,os,subprocess,sys
sys.path.insert(0,'lane')
import floatsafe
import family_step as F
os.makedirs('control-fq',exist_ok=True)
rows=list(csv.DictReader(open('control975.csv')));_,fr,score,why=floatsafe.work((975,rows));assert fr is not None,why
p='control-fq/975-control.csv'
with open(p,'w') as h:
 w=csv.DictWriter(h,['n','square_id','x','y','angle']);w.writeheader();w.writerows(fr)
credit=json.load(open('control975.source.json'))
json.dump(dict(n=975,built=(1+score)*(975**.5),source='held975 control, clean gather/round23-2026-11-13b.csv; '+credit['source'],licence=credit['licence']),open(p[:-4]+'.json','w'))
r=subprocess.run([sys.executable,'-I','quench22.py',p,'control-fq/975-out.csv']);assert r.returncode==0
j=json.load(open('control-fq/975-out.json'));q=j['certified_file_quench'];assert q['completed'] and q['invoked'] and q['returncode']==0
out=list(csv.DictReader(open('control-fq/975-out.csv')));_,fr2,score2,why=floatsafe.work((975,out));assert fr2 is not None,why
print('CONTROL real fq completed975, start',q['start'],'returned',q['end'],'certified score',score2,'invoked',q['invoked'],'returncode',q['returncode'],flush=True)
open('CONTROL_REAL_FQ_PASS','w').write(json.dumps(q))
