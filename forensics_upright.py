#!/usr/bin/env python3
"""Upright candidate centres at joint contacts of two fixed tilted squares.

fillfast starts with wall rows and columns. A small cavity can require both
coordinates to move away from those rows. Each tilted square excludes an
octagon of upright centres, its Minkowski sum with an upright unit square.
Intersections of neighbouring octagon edges provide candidates for such holes.
These are starts for a quench. Certification still uses floatsafe.

joint_candidates(side, T, tol=1e-6) returns (x, y, 0 degrees) rows.
install(fillfast, reach=32) adds isolated holes to that module's ordinary candidates.
"""
import math
import numpy as np
from scipy.spatial import ConvexHull, cKDTree

LAST = {}


def cross(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def joint_candidates(side, tilted, tol=1e-6):
    t = np.asarray(tilted, float).reshape(-1, 3)
    if not len(t):
        return np.empty((0, 3))
    off = np.array([[-.5, -.5], [.5, -.5], [.5, .5], [-.5, .5]])
    starts, vectors, normals, supports = [], [], [], []
    vertices = []
    for x, y, deg in t:
        angle = math.radians(deg)
        c, s = math.cos(angle), math.sin(angle)
        rotation = np.array([[c, -s], [s, c]])
        points = (off @ rotation.T)[:, None, :] + off[None, :, :]
        points = points.reshape(-1, 2)
        hull = ConvexHull(points)
        polygon = points[hull.vertices] + [x, y]
        starts.append(polygon)
        vectors.append(np.roll(polygon, -1, axis=0) - polygon)
        normal = np.zeros((8, 2)); support = np.full(8, np.inf)
        normal[:len(hull.equations)] = hull.equations[:, :2]
        support[:len(hull.equations)] = -hull.equations[:, 2]
        normals.append(normal); supports.append(support)
        vertices.extend(polygon)
    normals, supports = np.array(normals), np.array(supports)
    points = list(vertices)
    tree = cKDTree(t[:, :2])
    for i, j in sorted(tree.query_pairs(3.0)):
        a, u = starts[i][:, None, :], vectors[i][:, None, :]
        b, v = starts[j][None, :, :], vectors[j][None, :, :]
        denominator = cross(u, v)
        nonparallel = np.abs(denominator) > 1e-12
        safe = np.where(nonparallel, denominator, 1.)
        alpha, beta = cross(b - a, v) / safe, cross(b - a, u) / safe
        keep = nonparallel & (alpha >= -1e-9) & (alpha <= 1 + 1e-9) & (beta >= -1e-9) & (beta <= 1 + 1e-9)
        points.extend((a + alpha[..., None] * u)[keep])
    # Contacts with the containing walls are arrangement vertices too.
    for a, u in zip(starts, vectors):
        for axis in (0, 1):
            valid = np.abs(u[:, axis]) > 1e-12
            for wall in (.5, side - .5):
                alpha = (wall - a[:, axis]) / np.where(valid, u[:, axis], 1.)
                keep = valid & (alpha >= 0) & (alpha <= 1)
                points.extend((a + alpha[:, None] * u)[keep])
    p = np.asarray(points).reshape(-1, 2)
    p = p[(p.min(1) >= .5 - tol) & (p.max(1) <= side - .5 + tol)]
    unique = {}
    for row in p:
        unique.setdefault(tuple(np.round(row, 8)), row)
    p = np.asarray(list(unique.values())).reshape(-1, 2)
    near = tree.query_ball_point(p, 1.5)
    pi = np.repeat(np.arange(len(p)), [len(v) for v in near])
    ti = np.array([j for neighbors in near for j in neighbors], int)
    bad = np.zeros(len(p), bool)
    if len(pi):
        delta = p[pi] - t[ti, :2]
        slack = np.einsum('ij,ikj->ik', delta, normals[ti]) - supports[ti]
        bad[np.unique(pi[slack.max(1) < -tol])] = True
    out = np.c_[p[~bad], np.zeros(np.count_nonzero(~bad))]
    LAST.update(raw=len(points), distinct=len(p), valid=len(out))
    return out


def install(module, reach=32, minimum_distance=1.5):
    base = module.candidates

    def candidates(side, tilted, tau=0.):
        old = np.asarray(base(side, tilted, tau, reach=reach)).reshape(-1, 3)
        extra = joint_candidates(side, tilted, tol=max(1e-6, tau))
        # A point farther than sqrt(2) from every old upright candidate
        # cannot conflict with one. Keep the original candidate graph intact.
        if len(old) and len(extra):
            distance, _ = cKDTree(old[:, :2]).query(extra[:, :2])
            extra = extra[distance > minimum_distance]
        LAST.update(base=len(old), isolated=len(extra), combined=len(old) + len(extra))
        return list(old) + list(extra)

    module.candidates = candidates
