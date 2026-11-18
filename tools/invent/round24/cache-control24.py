import pathlib,subprocess,csv,shutil,hashlib,json,time,sys,os
W=pathlib.Path(__file__).resolve().parent;C=W/'cache-control24';C.mkdir(exist_ok=True);T=C/'take';T.mkdir(exist_ok=True)
control_bar=0.023899692787311855
# Preserve the external442 bar observed when this control first ran.
source=(W/'certrest24.py').read_text().replace('# CONTROL_OVERRIDE', f"held[442]={control_bar!r};held22[442]={control_bar!r};bar[442]={control_bar!r};freebar[442]={control_bar!r}")
(C/'certrest23.py').write_text(source.replace('save_cache()', 'pass'))
(C/'bar-at-control.json').write_text(json.dumps({'442':control_bar}))
raw=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r23/work/boxE-raw/f154520x442x28/final');PY=sys.executable
logs=[]
def run(args):
 p=subprocess.run([PY,'-I',str(C/'certrest23.py'),str(T)]+args,capture_output=True,text=True,check=True);logs.append(p.stdout+p.stderr);return list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
rs=run([str(raw)+'|cache positive control copied from fresh border442, exact source in production jobs.json|same donor licence as production job'])
assert len(rs)==1 and rs[0]['n']=='442',rs
before=(T/'take.tsv').read_bytes();run([]);assert(T/'take.tsv').read_bytes()==before
original=(T/'442.csv').read_bytes();original_stat=(T/'442.csv').stat();rows=list(csv.DictReader(open(T/'442.csv')))
for k in ['x','y','angle']:rows[1][k]=rows[0][k]
with open(T/'442.csv','w',newline='')as h:
 w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rows)
os.utime(T/'442.csv',ns=(original_stat.st_atime_ns,original_stat.st_mtime_ns))
rs=run([]);assert len(rs)==0,rs
(T/'442.csv').write_bytes(original);(T/'take.tsv').write_bytes(before)
rs=run([]);assert len(rs)==1 and(T/'take.tsv').read_bytes()==before
(C/'control.log').write_text('\n'.join(logs))
result={'positive':'one442 retained; cached pass byte-identical','negative':'overlapping cached442 dropped','restored':'same take.tsv bytes restored','sha256':hashlib.sha256(before).hexdigest()}
(C/'result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
