import pathlib,json
R=pathlib.Path.home()/'scratch/squares-k123';removed=0
for key in json.load(open(R/'archive-dry-keys26.json')):
 for p in (R/'out'/key).rglob('*.csv'):
  removed+=p.stat().st_size;p.unlink()
print(removed)
