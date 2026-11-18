# Copy close certified misses (within 1e-6 of score of the live bar, moved by the scan) to near/ with a source sidecar.
from common29 import *
base,live,_=bar();done=set(read(W/'near-published.json',[]));new=[]
for p in sorted((W/'near-unproved').glob('*.json')):
 if p.name in done:continue
 r=read(p,{});n=r['n'];score=r['score'];f=r['finish'];tag=p.stem.split('-',1)[1]
 if tag in read(W/'prohibited-tags.json',[]):continue  # 15:35Z: a prohibited source stays out of near/ too
 if score-live[n]>1e-6:done.add(p.name);continue
 if f.get('finish_best_raw','')==f.get('finish_start'):done.add(p.name);continue
 csvp=p.with_suffix('.csv');fr=[{k:x[k] for k in CSV} for x in csv.DictReader(open(csvp))];sc=score
 if not f.get('finish_quenched'):done.add(p.name);continue
 if fr is None:done.add(p.name);continue
 from prvsim29 import check
 # Own search outputs are exempt from the share gate.
 a=read(r['proof'],{})
 h=a.get('expanded',{}).get('history',{});review=read(W/'audited'/f'{tag}.json',{})
 if not review.get('accepted') and (h.get('issues') or h.get('excluded') or not h):continue
 from ancestor_share29 import inspect as ancestor_check
 anc=ancestor_check(r['proof'])
 if anc['excluded'] or anc['errors']:continue
 refs=[pair for pair in h.get('public',[]) if pair[0] not in ['Samanyu-dev/squares_in_squares','franciscouzo/square-packing']]
 proof_hash=hashlib.sha256(Path(r['proof']).read_bytes()).hexdigest();review=read(W/'public-root-reviews'/f'{proof_hash}.json',{})
 if refs and not (review.get('complete') and review.get('source_proof_sha256')==proof_hash):continue
 dst=T/'near'/f'{n}-classfill-{tag}.csv'
 with open(str(dst)+'.tmp','w',newline='') as h:w=csv.DictWriter(h,fieldnames=CSV);w.writeheader();w.writerows(fr)
 os.replace(str(dst)+'.tmp',dst)
 side=dict(n=n,score=sc,live_bar_at_copy=live[n],source=f"classfill r30 sigma0.02 first scan (midm_scan.py lkick,kick) and certified-file fq quench on {r['host']} of {a.get('input')}; input source: {a.get('source')}; immutable ancestry {r['proof']}",licence=f"Own scan; input licence: {a.get('licence')}",input_sha256=a.get('input_sha256'),ancestry=r['proof'])
 if f.get('finish_prequench'):
  from light29 import load as loadp
  from physical30 import key as physical_key
  original=W/'inputs'/f'{n}-{tag}.csv'
  side['prequench_parent']=True
  side['prepared_geometry_changed']=bool(original.exists() and physical_key(loadp(original,{n})[n])!=physical_key(loadp(dst,{n})[n]))
 atomic(Path(str(dst)+'.json'),side);done.add(p.name);new.append((n,sc,live[n],str(dst)))
atomic(W/'near-published.json',sorted(done))
for n,sc,lv,d in new:
 note(f'NEAR n{n} score{sc!r} live{lv!r} miss{sc-lv:.3g} {d}')
 hand(f'certified near n={n} score={sc!r} (miss {sc-lv:.3g} vs live bar), sidecar has source and licence, {d}')
print('NEAR',len(new))
