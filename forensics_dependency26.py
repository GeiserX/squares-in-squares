"""Filter previously admitted graphs after a source withdrawal.

This filter does not admit new sources. Publication still uses the complete
source checker. Reverse edges propagate a withdrawal through reference cycles.
"""
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_sources as fs


class Filter:
    def __init__(self, scratch):
        self.scratch = Path(scratch)
        self.edges = defaultdict(set)
        self.reasons = defaultdict(list)
        self.files = {}
        self.roots = {}
        self.bad = set()

    def document(self, path, expected=None):
        path = Path(path)
        key = 'file:'+str(path)
        if key in self.files:
            if expected and self.files[key] != expected:
                self.reasons[key].append('changed referenced hash')
            return key
        self.files[key] = None
        try:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            self.files[key] = digest
            if expected and digest != expected:
                self.reasons[key].append('changed referenced hash')
            self.visit(json.loads(data), key)
        except (OSError, ValueError, TypeError, RecursionError) as error:
            self.reasons[key].append('missing or unreadable reference: '+repr(error))
        return key

    def reference(self, owner, path, expected=None):
        if Path(path).suffix == '.json':
            self.edges[owner].add(self.document(path, expected))

    def visit(self, value, owner):
        if isinstance(value, dict):
            if fs.declared_withdrawal(value, self.scratch):
                self.reasons[owner].append('withdrawn identity '+str(value.get('path', value.get('source', value.get('origin')))))
            full = value.get('full_ancestry')
            if isinstance(full, dict) and full.get('path'):
                self.reference(owner, full['path'], full.get('sha256'))
            for field in ('source_proof', 'ancestry_file'):
                if isinstance(value.get(field), str):
                    expected = value.get('ancestry_sha256') if field == 'ancestry_file' else None
                    if value.get('reason') == 'verified immutable donor group':
                        expected = value.get('sha256')
                    self.reference(owner, value[field], expected)
            for child in value.values():
                self.visit(child, owner)
        elif isinstance(value, list):
            for child in value:
                self.visit(child, owner)
        elif isinstance(value, str):
            for path, n in fs.source_pairs(value):
                if fs.withdrawn(path, n, self.scratch):
                    self.reasons[owner].append('withdrawn source string '+str((path, n)))

    def packing(self, path, n):
        path = Path(path)
        token = (str(path), n)
        if token in self.roots:
            return self.roots[token]
        key = 'packing:'+str(n)+':'+str(path)
        self.roots[token] = key
        if fs.withdrawn(path, n, self.scratch):
            self.reasons[key].append('withdrawn packing identity')
            return key
        origin = Path(str(path)+'.origin.json')
        if origin.exists():
            try:
                data = json.loads(origin.read_bytes())
                if hashlib.sha256(path.read_bytes()).hexdigest() != data.get('snapshot_sha256'):
                    self.reasons[key].append('changed snapshot bytes')
            except (OSError, ValueError) as error:
                self.reasons[key].append(repr(error))
            self.edges[key].add(self.document(origin))
        else:
            try:
                ok, proof = fs.trace(path, n, self.scratch)
                self.visit(proof, key)
                if not ok:
                    self.reasons[key].append('source trace refused')
            except (OSError, ValueError, KeyError, RecursionError) as error:
                self.reasons[key].append(repr(error))
        return key

    def parts(self, parts, label):
        key = 'parts:'+label
        parents = []
        for tag in ('A', 'B', 'C'):
            if tag in parts:
                path, n = parts[tag]['source']
                parent = self.packing(path, int(n))
                self.edges[key].add(parent)
                parents.append(parent)
        if not parents:
            self.reasons[key].append('missing rectangle parents')
        return key

    def settle(self):
        reverse = defaultdict(set)
        for parent, children in self.edges.items():
            for child in children:
                reverse[child].add(parent)
        self.bad = {k for k, reasons in self.reasons.items() if reasons}
        queue = deque(self.bad)
        while queue:
            for parent in reverse[queue.popleft()]:
                if parent not in self.bad:
                    self.bad.add(parent)
                    queue.append(parent)
        return self.bad
