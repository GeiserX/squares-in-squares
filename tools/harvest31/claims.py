"""A backlog claim follows the exact input hash across path rewrites."""
import re


def claimed(path,key,lines):
    for line in lines:
        if 'backlog ->' not in line or 'claim' not in line.lower():continue
        hashes=re.findall(r'claims\s+\S*?-\d+-([0-9a-f]{12,64})(?=[\s,;]|$)',line,re.I)
        if hashes:
            if any(key.startswith(h) for h in hashes):return line
        elif str(path) in line:return line
    return None
