"""Rebind a mutable path while preserving hashes already recorded in its ancestry."""
import hashlib
from pathlib import Path
import re


def matches(path, expected):
    candidate = Path(path)
    return candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest().startswith(expected)


def replace_path(text, original, replacement, recover=None):
    pattern = re.compile(
        re.escape(original) + r'(?![\w./-])(?P<suffix>\s*\((?i:sha256) (?P<digest>[0-9a-fA-F]{12,64}))?',
    )

    def rewrite(match):
        expected = match['digest']
        if not expected:
            return replacement
        expected = expected.lower()
        if matches(replacement, expected):
            return replacement + match['suffix']
        if recover is None:
            from walker30 import byte_copy
            older = byte_copy(original, expected)
        else:
            older = recover(original, expected)
        if older and matches(older, expected):
            return str(older) + match['suffix']
        return match[0]

    return pattern.sub(rewrite, text)
