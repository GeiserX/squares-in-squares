"""Remove only verified, unstarted quench inputs dominated by a retained row."""
import csv,glob,hashlib,json,os,re,subprocess,sys
j=json.load(open(sys.argv[1]));active=set()
for line in subprocess.check_output(['ps','-ax','-o','command='],text=True).splitlines():
    match=re.search(r'(?:^|[ /])quench22.py\s+(cert-in/[^\s]+\.csv)',line)
    if match:active.add(match[1])
removed=[]
for p in sorted(glob.glob('cert-in/*.csv')):
    name=os.path.basename(p)[:-4]
    if p in active or os.path.exists('done/quench-'+name):continue
    n=int(name.split('-')[0]);known=j['files'].get(name)
    if str(n) not in j['retained'] or not known:continue
    if hashlib.sha256(open(p,'rb').read()).hexdigest()!=known['csv']:continue
    meta=p[:-4]+'.json'
    if not os.path.exists(meta) or hashlib.sha256(open(meta,'rb').read()).hexdigest()!=known['json']:continue
    # The certified start side is recorded by the producer before its quench.
    row=json.load(open(meta));score=float(row['built'])/(n**.5)-1
    if score<float(j['retained'][str(n)])-1e-10:continue
    os.remove(p);os.remove(meta);removed.append(name)
print(json.dumps(dict(removed=removed,protected_active=sorted(active),reason='dominated by retained certified row; exact local input hashes verified')),flush=True)
