import pathlib,json,os
R=pathlib.Path.home()/'scratch/squares-k123';d=json.load(open(R/'refused-inputs26.json'));D=R/'withdrawn-task26';D.mkdir(exist_ok=True);changed=[]
for p in (R/'tasks').glob('*.json'):
 j=json.load(open(p))
 if j.get('kind')!='scan':continue
 tag=j['tag'];bad=set(d.get(tag,[]));pairs=R/f'pairs-{tag}.txt'
 if not bad or not pairs.exists():continue
 old=pairs.read_text();keep=[z for z in old.split() if not set(z.split(','))&bad]
 (D/pairs.name).write_text(old);pairs.write_text(' '.join(keep));changed.append([tag,len(old.split()),len(keep)])
 if not keep:os.replace(p,D/p.name)
(R/'withdrawn-pair-filter26.json').write_text(json.dumps(changed));print('pending scans filtered',len(changed))
