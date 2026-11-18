import csv,json,pathlib,re
S=pathlib.Path('$SCRATCH/bounties-squares')
def lookup(p,n):
 lane=next((v for v in p.parts if v.startswith('take-')),'unknown')
 if lane.startswith('take-stair-c-'):
  key=p.stem.rsplit('-',1)
  if len(key)==2:
   jp=S/lane/'work/boxcopy'/key[1]/'raw-a'/(key[0]+'.json')
   if jp.exists():
    j=json.load(open(jp));mods=j['modules']
    return ('module build: '+', '.join(m['id']+' <'+m['source']+'>'for m in mods)+'; squeezed '+str(j.get('squeeze'))+'; exact build record '+str(jp),'; '.join(sorted(set(m['licence']for m in mods))))
 if lane.startswith(('take-readers-','take-family-')):
  m=re.match(r'^\d+-(up|down)(\d+)(c\d+)?from(.+)$',p.stem)
  if m:
   for table in [S/lane/'work/sources-all.tsv',S/lane/'work/sources.tsv']:
    if not table.exists():continue
    for row in csv.DictReader(open(table),delimiter='\t'):
     if row.get('donor')==m[4]:
      tool='family_readers.py'if lane.startswith('take-readers-')else'family_step.py'
      return (f'{tool} {m[2]} shell(s) {m[1]}, '+(f'cut {m[3][1:]}, 'if m[3]else'')+f'from {m[4]} <{row["source"]}>; exact source table {table}',row['licence'])
 return None
