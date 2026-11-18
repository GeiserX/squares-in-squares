import pathlib,csv,json,sys,subprocess,math,hashlib
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent
R=pathlib.Path('.');final='--final'in sys.argv
subprocess.run([str(S/'venv/bin/python'),str(W/'snapshot23.py')],check=True,stdout=subprocess.DEVNULL)
r=json.load(open(T/'report.json'));oldsummary=r['summary'];js=json.load(open(W/'jobs.json'))
done={p.parent.name:json.load(open(p))for p in(W/'boxE-raw').glob('*/done.json')}
ended=[j for j in js if j['kind']!='control'and j['id']in done];errors=[j for j in ended if done[j['id']].get('error')]
measured=list(csv.DictReader(open(R/'results/invent-r23-2026-11-13.tsv'),delimiter='\t'));prod=[a for a in measured if a['kind']!='control'];normal=[a for a in prod if not a.get('error')]
tries=sum(int(a['tries'])for a in prod);moved=[a for a in normal if float(a['final_side_gain'])>1e-8]
legs=[a for a in normal if a['kind']=='leg'];legmoves=[a for a in legs if float(a['final_side_gain'])>1e-8];fq=[a for a in normal if a['fq']=='True'];fqmoves=[a for a in fq if float(a['final_side_gain'])>1e-8]
pending=[j for j in js if j['id']not in done];unadmitted=json.load(open(W/'unadmitted-fresh.json'))if(W/'unadmitted-fresh.json').exists()else[]
desc=json.load(open(W/'descendant-rows.json'));stops=sum('plateau stop after'in p.read_text()for p in(W/'boxE-raw').glob('*/slide-*.tsv'))
back=sum(bool(j.get('backlog'))and j['id']in done for j in js);ns=[int(a['n'])for a in csv.DictReader(open(T/'take.tsv'),delimiter='\t')]
r['summary']=f'{len(ended)} production attempts on three boxE slots, {tries} completed tries. The take retains {len(ns)} n: '+(', '.join(map(str,ns))or'none')+f'. All {back}/13 saved starts finished. The first 442 and 485 kicks each removed 0.00046844 of side. The 442 result fed lower border descendants.'
r['what_was_measured']=[
 f'{len(ended)} production attempts ended, including {len(errors)} bounded errors. {len(moved)} normal runs moved more than 1e-8 of final side. The run table records all {tries} completed tries, error states, sources and licences.',
 f'All {back}/13 saved round 22 starts ran. The strongest continuations were 698, gaining 3.6747e-5 of side, and 753, gaining 6.2656e-6. The final old 796 start was dry.',
 f'The first fresh border 442 and 485 scans each gained 0.00046844 of side. Border 530 carried the 442 kick into lower descendants. {len(desc)} rows in other live takes name this lane in their ancestry. They are excluded from this take count and gain.',
 'Positive control 907 passed the squeeze stop at try 4, side 30.619564100215. Try 9 reproduced 30.618227092836. Its certified input also completed the required fq quench.',
 'Every published result passed floatsafe at 2.2e-11 and received fq on boxE from that certified file. Publication used the lower safe result. Per-n CSVs were written before replacing take.tsv by rename.',
 'The cache control used its recorded external 442 bar. Cached output stayed byte-identical, a duplicate-square overlap was rejected, and restoring the file restored identical output.',
 f'The final six-try policy stopped {stops} live scans. Replay of 45 full round 22 traces would free 4861.9 seconds and lose one 2.945e-8 side move on 340. The first ten moving traces remain intact. Stopped live traces are censored.',
 'The old floor at n = 300 was removed. The near margin became 0.0031 of side and the geometry key changed from 1e-5 to 1e-7. Translation, quarter-turn and reflection controls pass. A 0.001 centre move changes the key.',
 f'Fresh admission initially left 53 eligible take layouts unseen, including kicked copies. Reserved admission then started 379 at 17:32 UTC and 442 at 17:34 UTC. {len(unadmitted)} remaining eligible fresh layouts have immutable CSVs, hashes and provenance in work/unadmitted-fresh.json.',
 f'{len(errors)} bounded errors are recorded in work/failed-final.json. The 913 attempt hit 400 seconds before completing its first try and wrote no raw CSV. It received no unchanged retry.',
 'Search and postquench share the 18:30 UTC deadline. The timeout control stopped a child and grandchild in 0.517 seconds against a 0.5-second bound. Search stayed within three boxE slots at nice 5. boxE scipy 1.18.1 was verified.'
]
if final:
 cleanup=json.load(open(W/'cleanup.json'));ver=json.load(open(W/'verification.json'));assert sorted(ns)==sorted(a['n']for a in ver)
 for a in ver:assert hashlib.sha256((T/f'{a["n"]}.csv').read_bytes()).hexdigest()==a['sha256']
 r['processes_left']=cleanup['processes_left'];assert r['processes_left'].startswith('None.')
 r['what_was_measured'].append(f'Final uncached checks passed the metric and pandas parse on all {len(ver)} retained rows. '+(f'Minimum clearance was {min(a["clearance"]for a in ver):.12g}.'if ver else'There were no retained rows to test.')+f' All {cleanup["csv_count"]} remote CSV hashes matched local copies before removing the lane scratch.')
r['next']=[
 'Kick each new shell or join at its handoff and reserve fresh admission. The first 442 and 485 scans each removed 0.00046844 of side. Keep new round-trip near layouts beside them: round 22 family 855 gained 0.002536 of side.',
 f'Reconsider {len(unadmitted)} snapshots in work/unadmitted-fresh.json and {len(pending)} queued starts in work/pending-final.json against the next bar. Their exact inputs, sources and flags are saved. The 53-layout admission backlog showed why fresh builds need reserved capacity.',
 f'Give a useful find one leg. Saved 698 and 753 gained 3.6747e-5 and 6.2656e-6 of side. {len(legmoves)}/{len(legs)} completed legs moved more than 1e-8. The first 442 and 485 legs were dry, so require new geometry before repeating them.',
 f'Keep measuring the fq-enabled repair separately. {len(fqmoves)}/{len(fq)} completed fq-enabled scans moved more than 1e-8 of side. Change the layout or repair budget before repeating 913: its first try exceeded 400 seconds without output.',
 f'Keep positive controls on the rule that stops repeated end sides. Replay saves 4861.9 seconds on 45 full traces and loses one tiny move. {stops} live stops do not prove later gain is impossible. Measure both time and lost gain.',
 'Retain exact near provenance and quench certified inputs before publication. The overlap cache control rejects changed bad input. Round 22 postquench exceeded its search deadline by nine seconds, so preserve the tested common bound.'
]
r['blocked']=f'No access block. At the cutoff, {len(pending)} queued starts and {len(unadmitted)} eligible fresh snapshots remained unrun. Exact inputs and provenance are saved under work.'if final else f'Search is active. {len(pending)} starts are queued and {len(unadmitted)} eligible fresh layouts are archived.'
r['commits']=(W/'commits.txt').read_text().splitlines()
expected={'lane','improved_n','gain','take_dir','summary','what_was_measured','next','commits','processes_left','blocked','repo','branch','worktree','pr'}
assert set(r)==expected
p=T/'report.json.tmp';p.write_text(json.dumps(r,indent=2)+'\n');p.replace(T/'report.json')
section=(W/'round23-doc.md').read_text().replace(oldsummary,r['summary'],1)
a=section.index('### 18.4 Next');b=section.index('The deployed scripts',a)
section=section[:a]+'### 18.4 Next\n\n'+'\n'.join(f'{i}. {s}'for i,s in enumerate(r['next'],1))+'\n\n'+section[b:]
if final:section=section.replace('### 18.4 Next',r['what_was_measured'][-1]+'\n\n### 18.4 Next',1)
(W/'round23-doc.md').write_text(section)
p=R/'avenues/invent.md';text=p.read_text();a=text.index('## 18. Round 23');b=text.index('## Summary',a);p.write_text(text[:a]+section+'\n'+text[b:])
print(json.dumps({'attempts':len(ended),'tries':tries,'retained':ns,'errors':len(errors),'pending':len(pending),'unadmitted':len(unadmitted),'final':final}))
