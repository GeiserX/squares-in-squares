import csv,glob,json,os,sys,hashlib
sys.path.insert(0,'lane')
import modules as M

def recipe(j):
 try:return (int(j['n']),*[m['id'] for m in j['modules']],*j['stacks'])
 except (KeyError,TypeError):return None
old={recipe(json.load(open(p))) for p in glob.glob('hist/*.json')+glob.glob('raw-a/*.json')}
seen=set(); jobs=[]
for p in sys.argv[1:]:
 for r in csv.DictReader(open(p),delimiter='\t'):
  try:
   key=(int(r['n']),r['corner'],r['far1'],r['far2'],int(r['stacks1']),int(r['stacks2']))
   if key in old or key in seen or float(r['predicted_minus_held'])>.008:continue
  except (ValueError,KeyError,TypeError):continue
  seen.add(key);name=f'{key[0]}-sc23'+hashlib.sha256(repr(key).encode()).hexdigest()[:9]
  cmd=f'{name} ./py -I lane/modules.py job libbase raw-a details-r21.csv {name} '+str(key[0])+' '+' '.join(str(k) for k in key[1:])+f" {r['f']} --fq ./fq --squeeze family\n"
  jobs.append((float(r['predicted_minus_held']),cmd))
for _,cmd in sorted(jobs):print(cmd,end='')
print('fresh pending recipes',len(jobs),file=sys.stderr)
