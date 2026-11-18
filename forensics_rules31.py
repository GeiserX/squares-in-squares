"""Match the existing exclusions in bounded regions around required literals."""
import re
import hashlib
import time

ANCHORS={
 'penguin069 joegun union':('joegun',),
 'harvest-r22 a-row':('take-harvest-r22',),
 'areebbb a-row':('areebbb',),
 'r23 639':('take-invent-r23','take-midm-r23','round 23 file of n = 639 in'),
 'r22 745/858 join':('745r-858r','858r-745r','858-ec97a452','745-64c4b4f8'),
 'r23 forensics 980':('take-forensics-r23','round 23 file of n = 980 in take-forensics'),
 'older forensics 918':('take-forensics',),
}


# Changed or newly added rules always use the complete original expression.
KNOWN_PATTERN_SHA256={'penguin069 joegun union': 'd618bccf7453100edefae9c46db4499f04ddc6c13dfe0215d2e162528b340393', 'harvest-r22 a-row': '148a02c20b1e9f6ccc793564b8bbdc455f7436909da4b8e4b7ec2907c063a65a', 'areebbb a-row': '0a853a04629d9d65007d4a7312ae7ca9b6436859671e8198af34db0579725050', 'r23 639': 'a7db9cdc667b5a6348d70687a581b0a24ea995d6b06c09829db9eed71d83fac5', 'r22 745/858 join': '6f2227bd6b3c8c2e70d87d9679ca5457cd73e5b5f0606b2e17268f9c31ee65eb', 'r23 forensics 980': '16b76ebff9709157bc1acfb5ded600abe4915823f185414a877221e92c008666', 'older forensics 918': '2cc56d9982ae2d51b283ac32c4942c0f7b953f9cbec13b560cbc48263180356e'}


def regions(text,lower,anchors):
    intervals=[]
    for anchor in anchors:
        position=lower.find(anchor)
        while position>=0:
            a=max(0,position-512);b=min(len(text),position+len(anchor)+512)
            # The original expressions have unbounded whitespace around '='.
            # Extend a clipped whitespace run, then retain another whole margin.
            while a>0 and (text[a].isspace() or text[a-1].isspace() or text[a]=='='):
                while a>0 and text[a-1].isspace():a-=1
                a=max(0,a-512)
            while b<len(text) and (text[b-1].isspace() or text[b].isspace()):
                while b<len(text) and text[b].isspace():b+=1
                b=min(len(text),b+512)
            intervals.append((a,b));position=lower.find(anchor,position+len(anchor))
    start=end=None
    for a,b in sorted(intervals):
        if start is None:start,end=a,b
        elif a<=end:end=max(end,b)
        else:
            yield text[start:end]
            start,end=a,b
    if start is not None:yield text[start:end]


def hits(text,rules):
    selected=[(name,pattern) for name,pattern in rules if name!='prvsiyan best-of-1105']
    if not text.isascii():return [name for name,pattern in selected if re.search(pattern,text,re.I)]
    lower=text.lower();out=[]
    for name,pattern in selected:
        anchors=ANCHORS.get(name) if hashlib.sha256(pattern.encode()).hexdigest()==KNOWN_PATTERN_SHA256.get(name) else None
        if anchors is None:
            found=re.search(pattern,text,re.I)
        else:
            found=any(re.search(pattern,part,re.I) for part in regions(text,lower,anchors))
        if found:out.append(name)
    return out


def control():
    import quench_audit as q
    cases=['innocent metadata','squares-joegun-boxed','n = 639 from take-harvest-r22',
           'donor n = 745 of areebbb','take-midm-r23/639','round 23 file of n = 639 in elsewhere',
           '745r-858r','take-forensics-r23/980','round 23 file of n = 980 in take-forensics',
           'take-forensics-r22/918','round 22 file of n = 918 in take-forensics',
           'n'+' '*2000+'='+' '*2000+'639 from areebbb',
           'areebbb n'+' '*2000+'='+' '*2000+'639',
           'n = 639'+' '*1000+'areebbb','take-m\u0130dm-r23/639']
    for length in range(500,521):
        cases.extend(['n'+' '*2000+'='+' '*length+'639 from areebbb','areebbb n'+' '*length+'='+' '*2000+'639','n='+' '*length+'639 from areebbb'])
    for text in cases:
        expected=[name for name,pattern in q.RULES if name!='prvsiyan best-of-1105' and re.search(pattern,text,re.I)]
        assert hits(text,q.RULES)==expected,(text[:80],expected,hits(text,q.RULES))
    assert hits('NEW EXCLUSION',[('areebbb a-row','NEW EXCLUSION')])==['areebbb a-row']
    assert hits('NEW EXCLUSION',[('new rule','NEW EXCLUSION')])==['new rule']
    inert='benign source metadata; '*200000
    started=time.monotonic();assert not hits(inert,q.RULES);elapsed=time.monotonic()-started
    print('CONTROL existing-rule equivalence, long whitespace, negative distance and Unicode pass; bytes',len(inert),'seconds',elapsed,flush=True)


if __name__=='__main__':control()
