"""Build the lane table and new documentation from measured receipts."""
import json,csv,pathlib,sys
from provenance24 import W,R
j=json.load(open(W/'metrics25.json'));rows=j['rows']
lines=[
 '## 18. Round 25',
 '',
 f"The lane retained {len(rows)} clean certified source rows. They gain {j['gain_against_base']:.12g} against the final base bar.",
 f"At the final comparison, {len(j['lowest_n'])} rows beat every other live take by more than 1e-10. Their added gain is {j['gain_beyond_others']:.12g}.",
 '',
 f"The four boxE slots completed {j['attempts']} joins on {j['counts']} counts. There were {len(j['errors'])} refused rebuilds and {j['timeouts']} timed out jobs.",
 'The initial licensed pool ran first. Fresh layouts then stayed ahead of changed saved pairs and omitted partners.',
 'The largest returns came after the rebuilt 735 and 790 parents arrived. The parents and their licensed 968 descendant supplied the first new joins at 228, 365 and 534.',
 '',
 'Each source row passed floatsafe at 2.2e-11 clearance. Each received a boxE fq quench from its certified file before publication.',
 'Input geometry, source records and licences remain pinned in each pool. Complete ancestry is stored once by hash.',
 '',
 '| n | side | gain against base | gain beyond other takes |',
 '|---|---|---|---|',
]
for r in rows:lines.append(f"| {r['n']} | {r['side']:.12f} | {r['gain']:.12g} | {r['gain_beyond_others']:.12g} |")
lines += [
 '',
 'The first 534 source was withdrawn because its 172 parent had only a generic seed label.',
 'Its files remain quarantined outside the take and near folders. The later 534 uses the newly reconstructed licensed parents.',
 'Clean replacements bind both the CSV bytes and the new source record. Geometry alone does not establish source identity.',
 '',
 'The reader control exposed a median-angle error near 45 degrees. It transposed the rebuilt 735 away from its readable band.',
 'The fallback now checks the eight square symmetries when the original reader finds fewer than ten groups.',
 'Both rebuilt parents then read as 30 chains, with no side change. Existing readable orientations stay unchanged.',
 'The 444 replay printed 21.564693167754 before and after the change. Its reference is 21.564693168782.',
 '',
 'The old 968 seam on different normalized ends ended at 31.840227744147. The broad reader-fixed scan reached 31.604245473120.',
 'That is within 1.53e-9 of the clean rebuilt floor. The old 489 indices rebuilt 492 squares, so the worker refused that start.',
 '',
 'Source controls accepted the clean sources and rejected the withdrawn 534 and frozen 735 tree.',
 'A nested JSON control also rejected an unlicensed seed. The withdrawal cache retained the exact recorded path set.',
 'One thousand cached checks took 0.0603 seconds. The cache refreshes when the handoff log changes.',
 '',
 'Resident metadata controllers keep imports warm. Fresh admission takes priority over saved and deferred work.',
 'A clone filter skips admitted layouts whose coordinates differ by less than 1e-10. Its controls matched a 1e-11 clone and retained a 1e-8 change.',
 'The input transfer has a lock and a unique archive name. Missing files during a handoff no longer abort the staging pass.',
 '',
 'Next, join changed licensed ends and their fresh follower returns first. The rebuilt parents supplied all three new source counts.',
 'Keep the saved input and licence snapshots. The old 489 indices need a changed orientation or seam before another attempt.',
 'Keep the generic seed fallback closed. A missing source record remains a refusal.',
 '',
 'Sources and trials are in [the round table](../results/k123-r25-2026-11-14.tsv).',
 'The [round helpers](../tools/k123/r25/) run from the take work directory and read its archived source snapshots.',
 'Receipts and full input pools remain in `$SCRATCH/bounties-squares/take-k123-r25/work/`.',
 '',
]
lines += ['All lane workers stopped. boxE archive passed byte and checksum checks before its scratch directory was removed.', 'The shared boxE base was preserved.', '']
body='\n'.join(lines);(W/'round25-section.md').write_text(body)
if '--write' in sys.argv:
 p=R/'avenues/k123.md';text=p.read_text();mark='\n## 18. Round 25\n';text=text.split(mark)[0].rstrip()+'\n\n'+body;p.write_text(text)
 out=R/'results/k123-r25-2026-11-14.tsv'
 with open(out,'w',newline='') as f:
  fields=['kind','n','side','bar_side','base_score','new_score','gain_base','gain_beyond_others','pool','recipe','code','raw','source','licence']
  wr=csv.DictWriter(f,fieldnames=fields,delimiter='\t');wr.writeheader()
  for r in rows:wr.writerow(dict(kind='source',n=r['n'],side=r['side'],bar_side=(r['base_score']+1)*r['n']**.5,base_score=r['base_score'],new_score=r['score'],gain_base=r['gain'],gain_beyond_others=r['gain_beyond_others'],source=r['source'],licence=r['licence']))
  for l in (W/'records.jsonl').read_text().splitlines():
   r=json.loads(l);wr.writerow(dict(kind='trial',n=r['n'],side=r.get('side',''),bar_side=r.get('bar',''),pool=r['pool'],recipe=r['tag'],code=r.get('code',r.get('error','')),raw=r.get('raw',0)))
 print(out)
print('section',len(lines),'lines')
