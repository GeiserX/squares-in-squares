def select(partners,frac,levels,source_f,source_m,limit=7):
 productive=[295,367,752,788,965,985,804,808,442,928,790,630,988,450,703,462,500,540,376]
 order=sorted(partners,key=lambda n:(abs(frac[n]-source_f),abs(levels[n]-source_m),n))
 anchors=[n for n in productive if n in partners][:4]+order[:2]+[min(partners),max(partners)]
 out=[]
 for n in anchors+order:
  if n not in out:out.append(n)
  if len(out)>=limit:break
 return sorted(out)
