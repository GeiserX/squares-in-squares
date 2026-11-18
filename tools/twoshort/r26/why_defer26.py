import sys,json,re,pathlib
sys.path.insert(0,'$SCRATCH/bounties-squares/take-twoshort-r26/work')
import admit26
for line in open(sys.argv[1]):
    p=pathlib.Path(line.strip())
    if not p.exists():print('GONE',p);continue
    m=re.match(r'\d+',p.stem); n=int(m[0]) if m else 0
    try:
        ok,d=admit26.trace_input(p,n)
    except Exception as e:
        print('EXC',p,repr(e));continue
    errs=d.get('closure',{}).get('errors',[]) if isinstance(d,dict) else []
    reason=d.get('reason') if isinstance(d,dict) else None
    print('OK' if ok else 'NO',p.name if 'near' in str(p) else str(p).split('bounties-squares/')[-1],reason or '',json.dumps(errs[:3])[:500])
