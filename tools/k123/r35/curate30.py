"""Keep the final report focused on measured outcomes and controls."""
from pathlib import Path
import json, csv, time
W = Path(__file__).resolve().parent
p = W / 'measurements28.json'
backup = W / 'measurement-history30.json'
if not backup.exists(): backup.write_bytes(p.read_bytes())
rr = [json.loads(line) for line in (W / 'records.jsonl').read_text().splitlines()]
wide = [r for r in rr if r.get('mechanism')]
base, variant = {}, {}
for r in rr:
    if 'side' in r:
        (variant if r.get('mechanism') else base)[r['pool'], r['tag'], r['n']] = r
pairs = [variant[k]['side'] - base[k]['side'] for k in base.keys() & variant.keys()]
notes = [
    'The retained 295 came from default-finish 367r/584 intermediate j22b-fresh10054-367r-584-j11-19-s-5. Its 367 side was 19.689563650156, or 1.91076034312e-3 above the bar. Rejoining that non-winning end with held 295 gained 1.3613760239117312e-6 score.',
    'The 295 certificate has SHA256 8262a0387d745e4230c08da6d16f8e4d60f199c73fd05e3df61624d58e3a6344. Its full source walk has zero missing paths after recursive binding of the superseded quench 584 CSV and producer snapshots. Certificate coordinates stayed unchanged.',
    'Certified 295 side 17.69804292972446 differs from the stored board side 17.6980429294 by 3.2445868214381335e-10. This does not demonstrate an improvement over that board value.',
    'Producer controls accept own 756 and unrelated ledger updates. They reject changed target metadata and explicit excluded-publication ancestry. Own 985 and own 801 pass full source walks, with 801 taking 4.358410 s. Fetched public 551 fails at share 0.788. Own layouts retain the ownership allowance.',
    'Exact frozen 978 producer recovery passed packing and ledger hash controls, while a missing binding failed. Full 978/743 admission still rejects actual excluded 639 ancestry. Decimal filename suffixes no longer create false bare CSV edges. Genuine bare 921 references remain resolved.',
    'Queue CSVs and producer records are byte snapshots. Recursive source binding verifies their hashes and preserves live actions on the original bytes. Controls reject an exact withdrawn hash and a later action. A different hash and a later build remain allowed.',
    'External proof filenames can be structural keys. The binder verifies explicit packing and producer hashes and updates standalone digests only for content-addressed JSON. Wrong-packing-hash controls fail. Repairing two directory-path substitutions gave the unchanged 693 candidate a complete 68-file source walk with no missing files or exclusion hits.',
    'The finesafe 444 control gave ladder side 21.564693168781982 and bisected side 21.564693168202034. Clearance was 2.2001955812811502e-11 and the pandas metric check passed. The numerical 444 control reproduced 21.564693167754.',
    'A warm reader reduced a 43-file walk from 17.908711 s to 0.092038 s. Changed producer text still failed, and restoring it passed. Shared boxA load later reached 127.70 and a fresh pass exceeded 435 s. Fresh admission now saves timed-out records at 120 s without admitting them. Intermediate admission retains its 90 s budget. Actual 295 admission passed in 2.283807 s.',
    'The five-region selector retained all 381 baseline starts and produced 677. Baseline K4 also kept the winning 295 recipe, so the wider selector has no exclusive demonstrated bar gain. Scans retain an equal mix of baseline, three-region and five-region selection.',
    f'At {time.strftime("%H:%MZ", time.gmtime())}, the 1.005 finish had {len(wide)} attempts and {len(pairs)} matched recipe pairs. Of these pairs, {sum(d < -1e-8 for d in pairs)} ended lower and {sum(d > 1e-8 for d in pairs)} higher by more than 1e-8 of side. Early reductions reached 8.861538e-6 at 547 and 8.356927e-6 at 851. These finish deltas are not certified score gains.',
    'The 1.005 control reproduced the 444 reference exactly. This variant uses one physical slot with distinct claims, completion keys and source labels. Eleven intermediate method labels were corrected to the actual 1.005 finish. CSV bytes and original producer snapshots stayed unchanged.',
    'The changed 295/frozen 367 return ran five starts under each finish, ten trials in total, with no certificate. Its best 367 side was 19.688956051052. This shortened the old donor by 0.000607599104 but remained 1.3031612391181113e-3 above the bar.',
    'A controlled 295 proposal override retained all five baseline starts and added one target start. Certification bars and source rules stayed unchanged. Both 295 follow-up arms gave no retained gain. With the improved 367 donor, both finishes ended at 17.698042929361, only clearance-scale slack below the certified file.',
    'Twoshort claimed a 900 s kick of the exact 295 bytes at 13:54:07Z, within three minutes of publication. The k123 feeder skipped the duplicate. Its optional three 300 s legs use the existing scan slot and close intake at 16:35. The wrapper control relaxed inflated 444 from 21.569737320627016 to 21.564693167753934.',
    'An incomplete control-task upload stopped the scan worker once. Atomic task renames, incomplete-JSON retry and a light four-slot health check repaired the handoff. Partial and interrupted evidence remains in the archive. No fifth numerical slot was added.',
    'Original source snapshots remain preserved. The private reader includes round 30 proofs and actions, applies the two exact historical bare 921 corrections, and treats the exact conditional 08:40:36Z line as a retention note. Actual later actions still apply.'
]
csv.field_size_limit(1 << 28)
rows = list(csv.DictReader((W.parent / 'take.tsv').open(), delimiter='\t'))
row693 = next((r for r in rows if int(r['n']) == 693), None)
if row693:
    notes.append('Harvest followed the new 693 within about three minutes and lowered it by 3.040406149068531e-8 of score. Our wider-finish 454/693 join reached initial-certified score 0.017869452511380057, matching harvest within rounding. It added no gain beyond the live take and was not published as a new row.')
    notes.append('Rebuild claimed a 900 s kick of the exact 693 bytes at 17:27:20Z, 75 s after publication. K123 skipped a duplicate. Its own fresh join scan started at 17:26:27Z, 22 s after publication.')
    notes.append('The rescued 455r/693 join retained 693 at score ' + row693['new'] + ', gaining ' + row693['gain'] + ' against the round 30 bar. Its source-path repair changed no certificate coordinates. The normal certified-file quench and final verifier passed before publication.')
p.write_text(json.dumps(notes, indent=2) + '\n')
nexts = [
    'Return fresh non-winning bands as donors first. The 367 intermediate was 1.91e-3 above its own bar yet supplied the retained 295 gain of 1.3613760239117312e-6. Raw side proximity alone did not predict its usefulness.',
    'Join changed source-cleared endpoints and fresh rectangle returns, keeping every input and producer snapshot. Round 29 fresh 808/752 gave 3.368148203541921e-5. This round the changed 584/367 chain supplied 295. Completed unchanged geometry stays closed.',
    'Change topology before another identical 295/367 feedback pass. Ten 330/367 return trials gave no certificate. Both 295 follow-up arms also gave no lower retained score after relaxing the old board proximity filter.',
    'Keep source admission warm and separate from numerical work. The 43-file control fell from 17.908711 s to 0.092038 s while changed records still failed. Retry saved expensive identities after cache or load conditions change. Retain the 120 s fresh and 90 s intermediate budgets.',
    'Keep a controlled share of broader finishes until they demonstrate a retained gain. The 1.005 branch changes raw ends, but those deltas alone do not count against the bar. The wider selector retained 381 baseline starts and found 677, while 295 also survived baseline selection.',
    'Resume exact unrun recipes after changed fresh inputs. Keep method-specific completion keys and the stopped archive. Source recovery must match actual queued hashes. Public 551 at share 0.788 remains excluded.'
]
if row693:
    nexts[-1] += ' A resumed 455r/693 recipe supplied the second retained count after its exact source-path repair.'
(W / 'next28.json').write_text(json.dumps(nexts, indent=2) + '\n')
(W / 'owned-helpers26.json').write_text(json.dumps(sorted(p.name for p in W.glob('*.py'))) + '\n')
print('curated', len(notes), 'measurements and', len(nexts), 'measured next steps', flush=True)
