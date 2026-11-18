#!/usr/bin/env python3
"""Geometry checks for the corners lane's layout intake.

The importer compares coordinates and square angles under the eight symmetries
of a square. Equal side lengths alone do not identify a layout.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
import numpy as np
from scipy.spatial import cKDTree


def same_layout(first, second, tolerance=2e-9):
    """Compare radians-based layouts, independent of row order and box symmetry."""
    first, second = np.asarray(first, float).copy(), np.asarray(second, float).copy()
    if first.shape != second.shape or first.ndim != 2 or first.shape[1] != 3:
        return False
    if not np.isfinite(first).all() or not np.isfinite(second).all():
        return False
    first[:, :2] -= first[:, :2].mean(axis=0)
    second[:, :2] -= second[:, :2].mean(axis=0)
    tree = cKDTree(second[:, :2])
    vectors = np.column_stack((np.cos(first[:, 2]), np.sin(first[:, 2])))
    for flip in (1, -1):
        for turn in range(4):
            angle = turn * np.pi / 2
            rotation = np.array([[np.cos(angle), -np.sin(angle)],
                                 [np.sin(angle), np.cos(angle)]]) @ np.diag([flip, 1])
            positions = first[:, :2] @ rotation.T
            distance, index = tree.query(positions)
            if distance.max() > tolerance or len(np.unique(index)) != len(first):
                continue
            direction = vectors @ rotation.T
            angles = np.arctan2(direction[:, 1], direction[:, 0])
            error = (angles - second[index, 2] + np.pi / 4) % (np.pi / 2) - np.pi / 4
            if np.abs(error).max() <= tolerance:
                return True
    return False


class Layouts:
    """Keep each distinct geometry even when its side matches an existing one."""
    def __init__(self):
        self.by_count = {}

    def add(self, packing):
        packing = np.asarray(packing, float)
        previous = self.by_count.setdefault(len(packing), [])
        if any(same_layout(packing, other) for other in previous):
            return False
        previous.append(packing.copy())
        return True


def samanyu_seeds(source, licence=''):
    """Return named Samanyu seed counts, [] for no recorded link, or None.

    None means that the source names Samanyu but does not identify a seed count.
    The input must be the completed ancestry walk, not a layout's filename.
    """
    import re
    text = source + ' | ' + licence
    text = re.sub(r'Samanyu(?:-dev)?(?:\s+seed)?\s+ancestry\s*:\s*(?:none(?:\s+recorded)?|no|false)\b', '', text, flags=re.I)
    references = list(re.finditer(r'Samanyu-dev(?:/squares_in_squares)?', text, re.I))
    if not references:
        notice = re.search(r'Samanyu(?:-dev)?(?:\s+seed)?\s+ancestry:\s*(?:yes[^|]{0,60}?)?seed n\s*=\s*(\d+(?:\s*,\s*\d+)*)', text, re.I)
        if notice:
            return sorted(set(map(int, re.findall(r'\d+', notice[1]))))
        unmarked = re.sub(r'Samanyu seed ancestry:\s*none recorded', '', text, flags=re.I)
        return None if re.search(r'Samanyu', unmarked, re.I) else []
    counts = set()
    notice = re.search(r'Samanyu(?:-dev)?(?:\s+seed)?\s+ancestry:\s*(?:yes[^|]{0,60}?)?seed n\s*=\s*(\d+(?:\s*,\s*\d+)*)', text, re.I)
    if notice:
        counts.update(int(value) for value in re.findall(r'\d+', notice[1]))
    for match in references:
        before = text[max(0, match.start() - 100):match.start()]
        after = text[match.end():match.end() + 450].split('|', 1)[0].split('>', 1)[0]
        direct = re.search(r'n\s*=\s*(\d+)\s+of\s*$', before)
        if direct:
            counts.add(int(direct[1]))
        donor = re.search(r'(?:original seed,\s*)?(?:donor|seed) n\s*=\s*(\d+(?:\s*,\s*\d+)*)', after)
        if donor:
            counts.update(int(value) for value in re.findall(r'\d+', donor[1]))
    return sorted(counts) if counts else None


def samanyu_notice(seeds):
    """Write an explicit group marker for the assembler's licence column."""
    if seeds is None:
        return 'Samanyu seed ancestry: unresolved'
    if not seeds:
        return 'Samanyu seed ancestry: none recorded'
    return 'Samanyu seed ancestry: seed n = ' + ','.join(map(str, seeds))
