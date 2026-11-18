"""dupes30.py LIST PATH [PATH ...]: every file in LIST with the same bytes as PATH (size, then sha256)."""
import hashlib, os, sys
S = '$SCRATCH/bounties-squares/'
want = {}
for p in sys.argv[2:]:
    p = p if p.startswith('/') else S + p
    want.setdefault(os.path.getsize(p), {})[hashlib.sha256(open(p, 'rb').read()).hexdigest()] = p
for l in open(sys.argv[1]):
    f = l.strip()
    try:
        z = os.path.getsize(f)
    except OSError:
        continue
    if z in want:
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        if h in want[z]:
            print(want[z][h].replace(S, ''), '<=>', f.replace(S, ''), flush=True)
