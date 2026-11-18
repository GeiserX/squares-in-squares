"""review30.py KEY FIELD TEXT: set notes.json[KEY][FIELD] = TEXT (FIELD reviewed, blocked, walk_start, source, licence) and drop KEY from
autopub.json so the next autopub30 pass decides it again. Prints the note."""
import json, os, sys
W = '$SCRATCH/bounties-squares/take-rebuild-r31/work/'
k, f, t = sys.argv[1], sys.argv[2], sys.argv[3]
nf = W + 'notes.json'
notes = json.load(open(nf)) if os.path.isfile(nf) else {}
notes.setdefault(k, {})[f] = t
json.dump(notes, open(nf, 'w'), indent=1)
ap = json.load(open(W + 'autopub.json')) if os.path.isfile(W + 'autopub.json') else {}
ap.pop(k, None)
json.dump(ap, open(W + 'autopub.json', 'w'), indent=1)
print(json.dumps(notes[k])[:500])
