"""md_table.py: measure.tsv as the markdown table of the round section (donor, target, kind, starts, best give-back,
end minus live bar), sorted by end, the same columns as round 24."""
import csv,sys
from pathlib import Path
W=Path(__file__).parent
rows=list(csv.DictReader(open(W/'measure.tsv'),delimiter='\t'))
rows.sort(key=lambda r:float(r['end_minus_bar']))
print('| donor | target | kind | starts | best give-back | raw end minus live bar |')
print('|---|---|---|---|---|---|')
for r in rows:print(f"| {r['donor']} | {r['n']} | {r['kind']} | {r['starts']} | {float(r['giveback']):.7g} | {float(r['end_minus_bar']):.7g} |")
