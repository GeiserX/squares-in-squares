"""Keep withdrawal caches out of public source text while retaining every immutable proof edge."""
import json
MARK='pinned donor ancestry: '
def credits(records):
 out=[]
 for c in records:
  c={k:v for k,v in c.items() if k!='checked_paths'}
  if c.get('ancestry_file') and c.get('source','').startswith('licensed ancestry sha256 '):c['source']=c['source'].split(' | ',1)[0]
  out.append(c)
 return json.dumps(out,separators=(',',':'))
def source(text):
 if MARK not in text:return text
 prefix,tail=text.split(MARK,1)
 try:records,used=json.JSONDecoder().raw_decode(tail)
 except ValueError:return text
 if not isinstance(records,list):return text
 return prefix+MARK+credits(records)+tail[used:]
