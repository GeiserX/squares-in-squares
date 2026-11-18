"""Stage a soft-box island result of a border b1 endpoint for the certified-file fq (border r26, boxA, light).
Usage: isl_stage.py N IDENT
Pulls boxC isl/run/N/raw/, takes the smallest-side packing, runs floatsafe here, and when it certifies below the live bar
by more than 1e-10*sqrt(N) writes final/<uid>.job.json with the chain manifest IDENT (its b1 recipe is unchanged, so
verify_proofs.py checks the start, the certified input and the fq output as for any chain) and an island note that the
driver adds to the published source. Without a certified result below the bar it only logs the measurement."""
import sys,json,math,csv,hashlib,subprocess,time,re
from pathlib import Path
W=Path(__file__).parent;T=W.parent;S=T.parent
src=(W/'driver.py').read_text();src=src[:src.index("log('start round26 collector/scanner")]
src=src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_isl','__file__':str(W/'driver.py')};exec(compile(src,str(W/'driver.py'),'exec'),ns)
bs=ns['bs'];floatsafe=ns['floatsafe'];csvout=ns['csvout'];log=ns['log']
n=int(sys.argv[1]);ident=sys.argv[2]
L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
local=W/'isl'/str(n);local.mkdir(parents=True,exist_ok=True)
subprocess.run(['rsync','-a',f'boxC:scratch/squares-border-r26/isl/run/{n}/',str(local)+'/'],check=True)
best=None
for p in sorted((local/'raw').glob(f'{n}-*.csv')):
 rows=[r for r in csv.DictReader(open(p)) if int(r['n'])==n]
 _,fr,sc,e=floatsafe.work((n,rows))
 if fr is None:print(p.name,'does not certify',e);continue
 side=(sc+1)*math.sqrt(n);print(p.name,'certified side',repr(side),'bar',repr(L[n]),'gap',side-L[n])
 if best is None or sc<best[0]:best=(sc,fr,p)
if best is None:log(f'island {n}: no raw result certifies');sys.exit(0)
sc,fr,p=best;side=(sc+1)*math.sqrt(n)
if not side<L[n]-math.sqrt(n)*1e-10:
 log(f'island {n} ({ident}): best certified side {side:.12f} is {side-L[n]:.3e} above the bar {L[n]:.12f}; not staged');sys.exit(0)
man={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')};r=man[ident]
seeds=sorted(set(re.findall(rf'{n}-best-(\d+)\.csv',' '.join(x.name for x in (local/'raw').glob('*.csv')))))
note=(f'soft-box islands on the fq endpoint of this chain (lane methods_soft.py on boxC: 140 s at delta 2e-4 seed 11, 140 s at '
      f'1e-4 seed 12, then up to 1800 s at 2e-4 seed 13 with dry 360; best of seeds {",".join(seeds)}: {p.name}, floatsafe on boxA)')
uid=f'{ident}-isl-'+hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
csvout(W/'staged'/f'{uid}.csv',fr)
ss,AA=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr])
bs.write_txt(str(W/'final'/f'{uid}.input.txt'),ss,AA)
job=dict(input=f'{uid}.input.txt',output=f'{uid}.output.txt',n=n,manifest=r,certified_before=sc,island=note,
         chain={'mode':'b1, fq chain, then soft-box islands','s_start':ss,'log':[]})
(W/'final'/f'{uid}.job.json').write_text(json.dumps(job))
log(f'island {n} ({ident}): certified side {side:.12f}, {side-L[n]:.3e} against the bar {L[n]:.12f}; queued certified-file fq {uid}')
