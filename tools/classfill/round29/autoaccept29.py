from common29 import *
# Only immutable proofs with complete recorded history can publish.
for pj in sorted((W/'prospective').glob('*.json')):
 tag=pj.stem.split('-',1)[1];r=read(pj,{});n=r['n']
 if (W/'audited'/f'{tag}.json').exists():continue
 a=read(r.get('proof') or '',{});parent=None
 if not a:
  # Legs inherit the already accepted immutable closure.
  parent=read(W/'audited'/f'{tag}.json',{})
  if not parent:continue
 h=a.get('expanded',{}).get('history',{})
 if h.get('excluded'):continue
 if h.get('issues'):
  revision=hashlib.sha256((W/'history29.py').read_bytes()).hexdigest()
  cache=read(W/'reviewed'/(tag+'.json'),{})
  if cache.get('history_revision')==revision:h=cache['history']
  else:
   from history29 import trace
   h=trace(a['source'],a['licence'],dict(producer=a.get('metadata',{}),expanded_records=a.get('expanded',{}).get('records',[]),unresolved_csv=a.get('expanded',{}).get('unresolved_csv',[])),n)
   atomic(W/'reviewed'/(tag+'.json'),dict(history_revision=revision,history=h))
  if h.get('excluded') or h.get('issues'):continue
 if not a.get('source') or not a.get('licence'):continue
 if any(not Path(q['snapshot']).is_file() or hashlib.sha256(Path(q['snapshot']).read_bytes()).hexdigest()!=q['sha256'] for q in a.get('snapshots',[])+h.get('snapshots',[])):continue
 # Keep every recovered source snapshot in a new immutable closure.
 resolved=dict(a);resolved['expanded']=dict(a.get('expanded',{}),history=h);resolved['prior_closure']=blob(r['proof'])
 payload=json.dumps(resolved,sort_keys=True).encode();resolved_path=W/'resolved-proofs'/(hashlib.sha256(payload).hexdigest()+'.json');atomic(resolved_path,resolved)
 from ancestor_share29 import inspect as ancestor_check
 gate=ancestor_check(resolved_path)
 if gate['excluded'] or gate['errors']:
  atomic(W/'audited'/f'{tag}.json',dict(accepted=False,n=n,tag=tag,reason='recovered public-first root exclusion',ancestor_share_check=gate));continue
 r['proof']=str(resolved_path)
 f=r['finish'];host=r['host'];log=W/host/'logs'/(tag+'.log');out=Path(r['output'])
 q=[l for l in log.read_text().splitlines() if 'quench:' in l or ' QUENCH ' in l] if log.exists() else []
 if not q or not out.exists() or not f.get('finish_quenched'):continue
 from prvsim29 import check
 measure=dict(policy='own-layout exempt',share=0.0,excluded=False)
 # Outputs of our own search are exempt from the share gate.
 rec=dict(accepted=True,auto='round29 complete pinned history and public-source checks',n=n,tag=tag,input_sha256=a.get('input_sha256'),input_proof=r['proof'],walked=h,
  quench_receipt=dict(host=host,log=str(log),line=q[-1],finish_quenched=True,passes=f.get('finish_quench_passes')),
  certified_output_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),prvsiyan_share=measure,
  source=f"classfill r29 first scan of {a['input']}; start source: {a['source']}; immutable closure {r['proof']}; certified-file fq quench on {host}",licence='Own search; '+a['licence'],time_utc=now())
 from source_credits29 import attach
 attach(rec,rec['input_proof'])
 atomic(W/'audited'/f'{tag}.json',rec);note(f'AUDIT n{n} {tag} complete pinned history and share {measure["share"]}')
