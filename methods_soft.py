#!/usr/bin/env python3
"""Soft-box search: mutate, relax the overlap energy in a smaller box, legalise by LP.

The method is the one behind the public island GA for this competition
(grennwolf's notebook, after Jeroen Cottaar's Santa 2025 solution). This is our
own CPU version, written from its description:

  - the box is set DELTA below the best side, so every member overlaps a little;
  - a child is a copy of a member with one move (jiggle a square, jiggle or twist
    a cluster, turn a same-angle block rigidly, turn an upright square into the
    tilted row beside it), aimed 80% of the time at a square that overlaps;
  - the child is relaxed to a local minimum of
        E = sum over pairs of penetration^2 + 4 * sum of wall excess^2
    with L-BFGS (penetration = the smallest push on a separating axis);
  - the POP lowest energies survive (a child whose energy equals a member's to
    0.1% is a copy and is dropped);
  - when the best member has E below 1e-10 * n the box drops by DELTA again,
    so the island works below the legal side. Each time, that member is also
    legalised: relaxed hard in a ladder of boxes just above its own (+1e-5 to
    +2e-3), and the first overlap-free one is repaired and squeezed by
    methods_lp (exact LP). A legal side below the best becomes the new best.

Differences from the public GA: one island and no diversity rule, a compiled C
kernel on one core instead of CUDA (50 to 170 children a second at n = 701; the
numpy kernel makes about 5), and the legaliser ends in an exact LP after the
float64 relaxation ladder.

An island that makes no find in --restart children (3,000) starts again from its
legal best. With --dry S it ends S seconds after its last find (or its start). A mirror island (--start mbest, mdrop1) keeps every member symmetric
about the diagonal; its seed is settled to a soft-free symmetric packing first.

Usage: methods_soft.py SUB.csv OUTDIR --n 644   (SUB may be a raw per-n file of an earlier run)
       [--seconds 600] [--seed 1]
                       [--delta 2e-4] [--pop 12] [--moves row,ang,jig,clu,twi,blk,arm]
                       [--start best|drop1|drop2|mbest|mdrop1] [--restart 3000] [--dry 360]
                       [--kernel c|numpy] [--mirror-box settle|below] [--keep-softfree 1]
Output: OUTDIR/raw/<n>-<start>-<seed>.csv on every new best, OUTDIR/soft-<n>-<start>-<seed>.log.
        OUTDIR/softfree/<n>-<start>-<seed>-box<box>.csv: a member that is soft-free below the legal best
        and that the ladder could not make legal (not a result; the log line SOFTFREE-ILLEGAL has its true gap).
Only numpy and scipy are needed; the C kernel needs a system cc and falls back to numpy without one. Certification is methods_take.py.
"""
import argparse, csv, math, os, sys, time

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402

HALF_PI = math.pi / 2


C_SRC = r"""
#include <math.h>
#include <stdlib.h>
#include <string.h>
typedef long long i64;
static double sgn(double v) { return (v > 0) - (v < 0); }

/* E and its gradient G (n*3, zeroed here). C, S: cos and sin of every angle. Same axis order as
   methods_lp.best_axes: owner i with k = 0..3, then owner j, the first largest gap wins. */
static double energy_cs(const double *P, const double *C, const double *S, int n, double L,
                        const i64 *pairs, int m, const int *widx, int nw, double *G) {
    double E = 0.0;
    memset(G, 0, sizeof(double) * 3 * n);
    for (int p = 0; p < m; p++) {
        int i = (int)pairs[2 * p], j = (int)pairs[2 * p + 1];
        double ci = C[i], si = S[i], cj = C[j], sj = S[j];
        double dx = P[3 * j] - P[3 * i], dy = P[3 * j + 1] - P[3 * i + 1];
        double cd = cj * ci + sj * si, sd = sj * ci - cj * si;
        double off = 0.5 + 0.5 * (fabs(cd) + fabs(sd));
        double p0 = ci * dx + si * dy, p1 = -si * dx + ci * dy;
        double q0 = -(cj * dx + sj * dy), q1 = -(-sj * dx + cj * dy);
        double pr[8] = {p0, p1, -p0, -p1, q0, q1, -q0, -q1};
        int kb = 0; double g = pr[0];
        for (int k = 1; k < 8; k++) if (pr[k] > g) { g = pr[k]; kb = k; }
        g -= off;
        if (g >= 0) continue;
        int own = kb >> 2, k = kb & 3;
        int a = own ? j : i, b = own ? i : j;
        double ca = own ? cj : ci, sa = own ? sj : si;
        double ux, uy;
        if (k == 0) { ux = ca; uy = sa; } else if (k == 1) { ux = -sa; uy = ca; }
        else if (k == 2) { ux = -ca; uy = -sa; } else { ux = sa; uy = -ca; }
        double ce = cd, se = own ? -sd : sd, cp, sp;
        if (k == 0) { cp = ce; sp = se; } else if (k == 1) { cp = se; sp = -ce; }
        else if (k == 2) { cp = -ce; sp = -se; } else { cp = -se; sp = ce; }
        double dh = 0.5 * (-sgn(cp) * sp + sgn(sp) * cp);
        double ax = own ? -dx : dx, ay = own ? -dy : dy;
        double perp = -uy * ax + ux * ay;
        double pen = -g, w = -2 * pen;
        E += pen * pen;
        G[3 * b] += w * ux; G[3 * b + 1] += w * uy;
        G[3 * a] -= w * ux; G[3 * a + 1] -= w * uy;
        G[3 * a + 2] += w * (perp + dh); G[3 * b + 2] -= w * dh;
    }
    for (int q = 0; q < nw; q++) {
        int i = widx ? widx[q] : q;
        double c = C[i], s = S[i];
        double h = 0.5 * (fabs(c) + fabs(s)), dh = 0.5 * (-sgn(c) * s + sgn(s) * c);
        for (int k = 0; k < 2; k++) {
            double v = P[3 * i + k];
            double lo = h - v > 0 ? h - v : 0, hi = v + h - L > 0 ? v + h - L : 0;
            E += 4 * (lo * lo + hi * hi);
            G[3 * i + k] += 8 * (hi - lo);
            G[3 * i + 2] += 8 * (lo + hi) * dh;
        }
    }
    return E;
}

double soft_energy(const double *P, int n, double L, const i64 *pairs, int m,
                   const int *widx, int nw, double *G) {
    double *C = malloc(sizeof(double) * 2 * n), *S = C + n;
    for (int i = 0; i < n; i++) { C[i] = cos(P[3 * i + 2]); S[i] = sin(P[3 * i + 2]); }
    double E = energy_cs(P, C, S, n, L, pairs, m, widx, nw, G);
    free(C);
    return E;
}

#define MEM 8
/* L-BFGS over the squares idx[0..na) of P (in place); the others stay. Walls of widx (NULL = all n).
   Stops like scipy's L-BFGS-B on E*1e8 with ftol 1e-14: relative decrease below 1e-14 of max(E, 1e-8). */
double soft_relax(double *P, int n, double L, const i64 *pairs, int m, const int *idx, int na,
                  const int *widx, int nw, int maxiter, int *nfev) {
    int N = 3 * na, mem = 0, head = 0, ev = 0;
    double *buf = calloc((size_t)N * (5 + 2 * MEM) + 5 * (size_t)n, sizeof(double));
    double *x = buf, *g = x + N, *xn = g + N, *gn = xn + N, *d = gn + N;
    double *Sm = d + N, *Ym = Sm + (size_t)MEM * N, *C = Ym + (size_t)MEM * N, *S = C + n, *G = S + n;
    double rho[MEM], al[MEM];
    for (int i = 0; i < n; i++) { C[i] = cos(P[3 * i + 2]); S[i] = sin(P[3 * i + 2]); }
    for (int q = 0; q < na; q++) for (int k = 0; k < 3; k++) x[3 * q + k] = P[3 * idx[q] + k];
#define EVAL(X, GG, F) do { \
        for (int q = 0; q < na; q++) { int i = idx[q]; P[3 * i] = X[3 * q]; P[3 * i + 1] = X[3 * q + 1]; \
            P[3 * i + 2] = X[3 * q + 2]; C[i] = cos(X[3 * q + 2]); S[i] = sin(X[3 * q + 2]); } \
        F = energy_cs(P, C, S, n, L, pairs, m, widx, nw, G); ev++; \
        for (int q = 0; q < na; q++) { int i = idx[q]; GG[3 * q] = G[3 * i]; GG[3 * q + 1] = G[3 * i + 1]; \
            GG[3 * q + 2] = G[3 * i + 2]; } } while (0)
    double f, fn;
    EVAL(x, g, f);
    for (int it = 0; it < maxiter; it++) {
        double gmax = 0, gg = 0;
        for (int t = 0; t < N; t++) { double v = fabs(g[t]); if (v > gmax) gmax = v; gg += g[t] * g[t]; }
        if (gmax <= 1e-21) break;
        memcpy(d, g, sizeof(double) * N);
        for (int c = 0; c < mem; c++) {
            int k = (head - 1 - c + MEM) % MEM; double *s = Sm + (size_t)k * N, *y = Ym + (size_t)k * N, a = 0;
            for (int t = 0; t < N; t++) a += s[t] * d[t];
            a *= rho[k]; al[k] = a;
            for (int t = 0; t < N; t++) d[t] -= a * y[t];
        }
        if (mem) {
            int k = (head - 1 + MEM) % MEM; double *s = Sm + (size_t)k * N, *y = Ym + (size_t)k * N, sy = 0, yy = 0;
            for (int t = 0; t < N; t++) { sy += s[t] * y[t]; yy += y[t] * y[t]; }
            double gam = sy / yy;
            for (int t = 0; t < N; t++) d[t] *= gam;
        }
        for (int c = mem - 1; c >= 0; c--) {
            int k = (head - 1 - c + MEM) % MEM; double *s = Sm + (size_t)k * N, *y = Ym + (size_t)k * N, b = 0;
            for (int t = 0; t < N; t++) b += y[t] * d[t];
            b *= rho[k];
            for (int t = 0; t < N; t++) d[t] += (al[k] - b) * s[t];
        }
        double dg = 0;
        for (int t = 0; t < N; t++) { d[t] = -d[t]; dg += d[t] * g[t]; }
        if (!(dg < 0)) { mem = 0; dg = -gg; for (int t = 0; t < N; t++) d[t] = -g[t]; }
        double step = 1.0;
        if (!mem) { double gn2 = sqrt(gg); step = gn2 > 1 ? 1 / gn2 : 1.0; }
        int ok = 0;
        for (int ls = 0; ls < 40; ls++) {
            for (int t = 0; t < N; t++) xn[t] = x[t] + step * d[t];
            EVAL(xn, gn, fn);
            if (fn <= f + 1e-4 * step * dg) { ok = 1; break; }
            double den = 2 * (fn - f - dg * step), st = den > 0 ? -dg * step * step / den : 0.5 * step;
            if (st < 0.1 * step) st = 0.1 * step;
            if (st > 0.5 * step) st = 0.5 * step;
            step = st;
        }
        if (!ok) {
            if (mem) { mem = 0; it--; if (ev > 20 * maxiter) break; continue; }   /* try again along -g */
            break;
        }
        double *s = Sm + (size_t)head * N, *y = Ym + (size_t)head * N, sy = 0, ss = 0, yy = 0;
        for (int t = 0; t < N; t++) { s[t] = xn[t] - x[t]; y[t] = gn[t] - g[t]; sy += s[t] * y[t]; ss += s[t] * s[t]; yy += y[t] * y[t]; }
        if (sy > 1e-10 * sqrt(ss * yy) && sy > 0) { rho[head] = 1 / sy; head = (head + 1) % MEM; if (mem < MEM) mem++; }
        double fo = f, big = fo > 1e-8 ? fo : 1e-8;
        memcpy(x, xn, sizeof(double) * N); memcpy(g, gn, sizeof(double) * N); f = fn;
        if (fo - fn <= 1e-14 * big) break;
    }
    { double *gt = gn; EVAL(x, gt, f); }
    if (nfev) *nfev = ev;
    free(buf);
    return f;
}
"""

KERN = None      # the compiled kernel (ctypes), or None: numpy and scipy do the work


def load_kernel():
    """Compile C_SRC with the system cc into the temp dir (once per source hash) and load it."""
    global KERN
    import ctypes, hashlib, subprocess, tempfile
    tag = hashlib.sha256(C_SRC.encode()).hexdigest()[:16]
    so = os.path.join(tempfile.gettempdir(), 'methods_soft-%s-%d.so' % (tag, os.getuid()))
    try:
        if not os.path.exists(so):
            src = '%s.%d.c' % (so, os.getpid())
            open(src, 'w').write(C_SRC)
            subprocess.check_call(['cc', '-O3', '-shared', '-fPIC', '-o', src + '.so', src, '-lm'])
            os.replace(src + '.so', so); os.remove(src)
        lib = ctypes.CDLL(so)
    except Exception as e:      # no compiler on this box: the numpy path still works
        print('kernel not built (%s): numpy path' % e, file=sys.stderr)
        return False
    dp = np.ctypeslib.ndpointer(np.float64, flags='C_CONTIGUOUS')
    lp = np.ctypeslib.ndpointer(np.int64, flags='C_CONTIGUOUS')
    vp = ctypes.c_void_p
    lib.soft_energy.restype = ctypes.c_double
    lib.soft_energy.argtypes = [dp, ctypes.c_int, ctypes.c_double, lp, ctypes.c_int, vp, ctypes.c_int, dp]
    lib.soft_relax.restype = ctypes.c_double
    lib.soft_relax.argtypes = [dp, ctypes.c_int, ctypes.c_double, lp, ctypes.c_int, vp, ctypes.c_int,
                               vp, ctypes.c_int, ctypes.c_int, vp]
    KERN = lib
    return True


def _ip(idx):
    a = np.ascontiguousarray(idx, np.int32)
    return a, a.ctypes.data


def c_energy(P, L, pairs, widx=None):
    n = len(P)
    P = np.ascontiguousarray(P, np.float64); G = np.empty((n, 3))
    pr = np.ascontiguousarray(pairs, np.int64).reshape(-1, 2)
    if widx is None:
        E = KERN.soft_energy(P, n, L, pr, len(pr), None, n, G)
    else:
        w, wp = _ip(widx)
        E = KERN.soft_energy(P, n, L, pr, len(pr), wp, len(w), G)
    return E, G


def c_relax(P, L, pairs, idx, maxiter):
    """L-BFGS in C over the squares idx (None = all). Returns (P, E of the pairs and walls given)."""
    n = len(P)
    Q = np.array(P, np.float64, order='C')
    pr = np.ascontiguousarray(pairs, np.int64).reshape(-1, 2)
    if idx is None:
        idx = np.arange(n)
        a, ap = _ip(idx)
        E = KERN.soft_relax(Q, n, L, pr, len(pr), ap, n, None, n, maxiter, None)
    else:
        a, ap = _ip(idx)
        E = KERN.soft_relax(Q, n, L, pr, len(pr), ap, len(a), ap, len(a), maxiter, None)
    return Q, E


def energy(v, n, L, pairs, widx=None):
    P = v.reshape(n, 3)
    G = np.zeros((n, 3))
    E = 0.0
    if len(pairs):
        g, A, B, PHI = mlp.best_axes(P, pairs)
        m = g < 0
        if m.any():
            a, b, phi, pen = A[m], B[m], PHI[m], -g[m]
            ux, uy = np.cos(phi), np.sin(phi)
            dx, dy = P[b, 0] - P[a, 0], P[b, 1] - P[a, 1]
            psi = P[b, 2] - phi
            cp, sp = np.cos(psi), np.sin(psi)
            dh = 0.5 * (-np.sign(cp) * sp + np.sign(sp) * cp)
            perp = -uy * dx + ux * dy
            E += float((pen ** 2).sum())
            w = -2 * pen                      # dE/dg
            np.add.at(G[:, 0], b, w * ux); np.add.at(G[:, 1], b, w * uy)
            np.add.at(G[:, 0], a, -w * ux); np.add.at(G[:, 1], a, -w * uy)
            np.add.at(G[:, 2], a, w * (perp + dh)); np.add.at(G[:, 2], b, -w * dh)
    W = P if widx is None else P[widx]
    th = W[:, 2]
    c, s = np.cos(th), np.sin(th)
    h = 0.5 * (np.abs(c) + np.abs(s))
    dh = 0.5 * (-np.sign(c) * s + np.sign(s) * c)
    GW = np.zeros((len(W), 3))
    for k in (0, 1):
        lo = np.maximum(0, h - W[:, k]); hi = np.maximum(0, W[:, k] + h - L)
        E += 4 * float((lo ** 2).sum() + (hi ** 2).sum())
        GW[:, k] += 8 * (hi - lo)
        GW[:, 2] += 8 * (lo + hi) * dh
    if widx is None:
        G += GW
    else:
        G[widx] += GW
    return E, G.ravel()


def local_energy(P, L, act):
    """The part of E that involves an active square: its pairs and its walls."""
    pairs = mlp.pair_list(P, math.sqrt(2) + 0.01)
    pairs = pairs[act[pairs[:, 0]] | act[pairs[:, 1]]]
    if KERN is not None:
        return c_energy(P, L, pairs, np.nonzero(act)[0])[0]
    return energy(P.ravel(), len(P), L, pairs, np.nonzero(act)[0])[0]


def relax_local(P, L, act, maxiter=200):
    """Relax only the active squares; the others stay where they are. Returns (P, local E)."""
    n = len(P)
    idx = np.nonzero(act)[0]
    pairs = mlp.pair_list(P, math.sqrt(2) + 0.2)
    pairs = pairs[act[pairs[:, 0]] | act[pairs[:, 1]]]
    if KERN is not None:
        Q, _ = c_relax(P, L, pairs, idx, maxiter)
        return Q, local_energy(Q, L, act)
    W = P.copy()

    def f(v):
        W[idx] = v.reshape(-1, 3)
        E, G = energy(W.ravel(), n, L, pairs, idx)
        return E * SCALE, G.reshape(n, 3)[idx].ravel() * SCALE
    r = minimize(f, P[idx].ravel(), jac=True, method='L-BFGS-B',
                 options={'maxiter': maxiter, 'maxcor': 8, 'ftol': 1e-14, 'gtol': 1e-13})
    Q = P.copy(); Q[idx] = r.x.reshape(-1, 3)
    return Q, local_energy(Q, L, act)


def active_set(P, Q, radius=2.5, tol=0.0, h=0):
    """Squares within radius of a square that the move changed (by more than tol).
    h > 0 is a mirror state [A (h), B (h), D]: a square is active when it or its mirror image is,
    so the symmetrisation after a relaxation moves active squares only."""
    from scipy.spatial import cKDTree
    ch = np.nonzero(np.abs(Q - P).sum(1) > tol)[0]
    if not len(ch):
        return None
    act = np.zeros(len(P), bool)
    tree = cKDTree(Q[:, :2])
    for lst in tree.query_ball_point(Q[ch, :2], radius):
        act[lst] = True
    if h:
        both = act[:h] | act[h:2 * h]
        act[:h] = both; act[h:2 * h] = both
    return act


def overlap_weight(P, L):
    """Per square: its deepest penetration with a neighbour or a wall."""
    n = len(P)
    w = np.zeros(n)
    pairs = mlp.pair_list(P, math.sqrt(2) + 0.05)
    if len(pairs):
        g, A, B, _ = mlp.best_axes(P, pairs)
        pen = np.maximum(0, -g)
        np.maximum.at(w, A, pen); np.maximum.at(w, B, pen)
    h = mlp.half(P[:, 2])
    for k in (0, 1):
        w = np.maximum(w, np.maximum(h - P[:, k], P[:, k] + h - L))
    return np.maximum(w, 0)


SCALE = 1e8      # L-BFGS-B stops on the decrease relative to max(|E|, 1), so E is scaled up for it


def _scaled(v, n, L, pairs):
    E, G = energy(v, n, L, pairs)
    return E * SCALE, G * SCALE


def relax(P, L, maxiter=200):
    n = len(P)
    pairs = mlp.pair_list(P, math.sqrt(2) + 0.2)
    if KERN is not None:
        return c_relax(P, L, pairs, None, maxiter)
    r = minimize(_scaled, P.ravel(), args=(n, L, pairs), jac=True, method='L-BFGS-B',
                 options={'maxiter': maxiter, 'maxcor': 8, 'ftol': 1e-14, 'gtol': 1e-13})
    Q = r.x.reshape(n, 3)
    return Q, float(r.fun) / SCALE


LADDER = (1e-5, 3e-5, 1e-4, 2e-4, 5e-4, 1e-3, 2e-3)


def ladder(Q, box, Lbest):
    """Legalise a soft-free state: relax it hard in boxes a little above its own,
    and repair the first one that comes out overlap-free (to 1e-7) with the exact
    fixed-angle LP. Returns (P, side) below Lbest, or None."""
    for off in LADDER:
        if box + off >= Lbest - 1e-9:
            return None
        R, E = relax(Q, box + off, 1500)
        if E > 1e-13:
            continue
        R, LR = mlp.reclose(R, 0.02)
        if mlp.min_gap(R) >= 2.5e-11 and LR < Lbest - 1e-9:
            return R, LR
    return None


# new island bests per 10,000 children, as the public notebook measured them on an RTX 5090
MOVE_W = {'row': 4.56, 'ang': 3.98, 'jig': 5.15, 'twi': 2.33, 'clu': 1.65, 'arm': 2.0, 'blk': 1.0}


def WEIGHTS(moves):
    w = np.array([MOVE_W.get(m, 1.0) for m in moves])
    return w / w.sum()


def drop_seed(sub, n, rng, k=1):
    """The held packing of n+k with k random squares removed: legal for n at the larger side."""
    P = mlp.normal(mlp.load(sub, {n + k})[n + k])
    keep = np.sort(rng.choice(n + k, n, replace=False))
    return P[keep]


def mirror_of(A):
    return np.column_stack([A[:, 1], A[:, 0], HALF_PI - A[:, 2]])


QUARTER_PI = math.pi / 4


def sym_fix(Q, h):
    """Make Q = [A (h squares), B (h), D (on the diagonal)] exactly symmetric about y = x:
    A and the mirror image of B are averaged, a D square goes onto the diagonal at the
    nearest angle that is its own mirror image (a multiple of 45 degrees)."""
    Q = Q.copy()
    A = 0.5 * (Q[:h] + mirror_of(Q[h:2 * h]))
    Q[:h] = A; Q[h:2 * h] = mirror_of(A)
    D = Q[2 * h:]
    c = 0.5 * (D[:, 0] + D[:, 1])
    D[:, 0] = c; D[:, 1] = c; D[:, 2] = np.round(D[:, 2] / QUARTER_PI) * QUARTER_PI
    return Q


def total_energy(P, L):
    pairs = mlp.pair_list(P, math.sqrt(2) + 0.2)
    if KERN is not None:
        return c_energy(P, L, pairs)[0]
    return energy(P.ravel(), len(P), L, pairs)[0]


SYM_CHUNK = 40


def sym_relax(P, L, h, maxiter, act=None):
    """Relax a symmetric state and keep it symmetric. A free relaxation leaves the symmetric
    subspace where that is unstable (a square on the diagonal squeezed by a mirror pair slides
    off to one side), so it runs in chunks of SYM_CHUNK steps with an exact symmetrisation after each.
    Returns (Q, E of the symmetric Q): the whole E, or the local E of act."""
    Q = P; E = math.inf
    for _ in range(max(1, maxiter // SYM_CHUNK)):
        if act is None:
            Q, _ = relax(Q, L, SYM_CHUNK)
        else:
            Q, _ = relax_local(Q, L, act, SYM_CHUNK)
        Q = sym_fix(Q, h)
        E1 = total_energy(Q, L) if act is None else local_energy(Q, L, act)
        done = E1 < 1e-16 or E1 > E * (1 - 1e-6)
        E = E1
        if done:
            break
    return Q, E


def mirror_candidate(P, n, side_, tau):
    """A symmetric layout of n squares from P (any count >= about n): the squares farther than
    tau from the diagonal on one side, their mirror images, and the squares within tau put on
    the diagonal. Squares are dropped, the deepest overlap first, until n are left.
    Returns (S, h) or None when P gives fewer than n."""
    d = (P[:, 0] - P[:, 1]) / math.sqrt(2)
    H = P[d >= tau] if side_ > 0 else mirror_of(P[d <= -tau])
    D = P[np.abs(d) < tau]
    h = len(H)
    S = sym_fix(np.vstack([H, mirror_of(H), D]), h)
    L = mlp.side(P)
    while len(S) > n:
        w = overlap_weight(S, L)
        extra = len(S) - n
        nd = len(S) - 2 * h
        if nd and (extra % 2 or extra >= 1 and w[2 * h:].max() >= w[:2 * h].max() or h == 0):
            k = 2 * h + int(np.argmax(w[2 * h:]))
            if extra % 2 == 0 and nd < 2:
                k = None
            if k is not None:
                S = np.delete(S, k, 0); continue
        if extra < 2 or h == 0:
            return None
        k = int(np.argmax(w[:h] + w[h:2 * h]))
        S = np.delete(S, [k, h + k], 0); h -= 1
    if len(S) != n:
        return None
    return S, h


def mirror_settle(S, h, L0, n, delta, log=None):
    """Make a symmetric layout overlap-free and then as small as it goes, before the island starts.
    The box starts wide enough for the layout to come apart (the centres are scaled with it), then
    shrinks in steps that halve each time the layout does not relax to soft-free.
    Returns (Q, box): Q is symmetric and soft-free at box. None if it never came apart."""
    free = 1e-10 * n
    Q = None
    for lift in (0.0, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0):
        box = L0 + lift
        R = S.copy(); R[:, :2] *= box / L0
        R, E = sym_relax(R, box, h, 3000)
        if E < free:
            Q = R; break
    if Q is None:
        return None
    step = max(0.3 * (box - L0), 4e-3)
    while step >= delta:
        b2 = box - step
        R = Q.copy(); R[:, :2] *= b2 / box
        R, E = sym_relax(R, b2, h, 3000)
        if E < free:
            Q, box = R, b2
        else:
            step *= 0.5
    return Q, box


def mirror_seed(sub, n, sources, delta, log, Lbest):
    """The best symmetric start for n: every candidate from the held n, n+1 and n+2, both sides of
    the diagonal and three widths of the diagonal strip, settled, the smallest soft-free box wins."""
    best = None
    held = mlp.load(sub, {n + k for k in sources})
    for k in sources:
        if n + k not in held:
            continue
        P = mlp.normal(held[n + k]); L0 = mlp.side(P)
        for side_ in (1, -1):
            for tau in (0.2, 0.35, 0.5):
                c = mirror_candidate(P, n, side_, tau)
                if c is None:
                    continue
                S, h = c
                r = mirror_settle(S, h, L0, n, delta)
                log('mirror seed: from n+%d side %+d strip %.2f pairs %d diagonal %d -> %s' % (
                    k, side_, tau, h, n - 2 * h, 'never came apart' if r is None else 'soft-free at box %.9f' % r[1]))
                if r is not None and (best is None or r[1] < best[1]):
                    best = (r[0], r[1], h)
                if best is not None and best[1] <= Lbest + delta:
                    return best          # as small as the legal best: no need to try the others
    return best


def project(Q, parent, h):
    """Make a child exactly mirror-symmetric again; the half that the move changed more leads."""
    da = np.abs(Q[:h] - parent[:h]).sum(); db = np.abs(Q[h:2 * h] - parent[h:2 * h]).sum()
    if db > da:
        Q[:h] = mirror_of(Q[h:2 * h])
    else:
        Q[h:2 * h] = mirror_of(Q[:h])
    return sym_fix(Q, h)


def tilt(th):
    """Angle folded to (-45, 45] degrees, in radians."""
    f = np.mod(th, HALF_PI)
    return np.where(f > HALF_PI / 2, f - HALF_PI, f)


def mutate(P, L, w, rng, moves):
    Q = P.copy()
    n = len(Q)
    if rng.random() < 0.8 and w.sum() > 0:
        # spread the weight to the squares around an overlap
        k = rng.choice(n, p=w / w.sum())
        d = np.hypot(Q[:, 0] - Q[k, 0], Q[:, 1] - Q[k, 1])
        near = np.nonzero(d < 2.0)[0]
        k = int(rng.choice(near))
    else:
        k = int(rng.integers(n))
    d = np.hypot(Q[:, 0] - Q[k, 0], Q[:, 1] - Q[k, 1])
    mv = moves[rng.choice(len(moves), p=WEIGHTS(moves))]
    if mv == 'jig':
        big = rng.random() < 0.3
        Q[k, :2] += rng.uniform(-1, 1, 2) * (0.1 if big else 0.05)
        Q[k, 2] += rng.uniform(-1, 1) * (math.pi if big else math.pi / 6)
    elif mv == 'clu':
        sel = d < rng.uniform(1.0, 2.5)
        Q[sel, :2] += rng.uniform(-1, 1, 2) * 0.05
        Q[sel, 2] += rng.uniform(-1, 1, sel.sum()) * 0.05
    elif mv == 'twi':
        R = rng.uniform(1.5, 4.0); a = math.radians(rng.uniform(-3, 3))
        f = np.maximum(0, 1 - d / R) * a
        dx, dy = Q[:, 0] - Q[k, 0], Q[:, 1] - Q[k, 1]
        Q[:, 0] = Q[k, 0] + np.cos(f) * dx - np.sin(f) * dy
        Q[:, 1] = Q[k, 1] + np.sin(f) * dx + np.cos(f) * dy
        Q[:, 2] += f
    elif mv == 'blk':
        t = tilt(Q[:, 2])
        same = np.abs(t - t[k]) < math.radians(0.5)
        order = np.argsort(d)
        size = int(rng.integers(4, 41))
        sel = [i for i in order[:size * 2] if same[i]][:size]
        if len(sel) < 2:
            return None, mv
        sel = np.array(sel)
        a = math.radians(rng.uniform(0.5, 3) * rng.choice([-1, 1]))
        c0 = Q[sel, :2].mean(0)
        dx, dy = Q[sel, 0] - c0[0], Q[sel, 1] - c0[1]
        Q[sel, 0] = c0[0] + math.cos(a) * dx - math.sin(a) * dy
        Q[sel, 1] = c0[1] + math.sin(a) * dx + math.cos(a) * dy
        Q[sel, 2] += a
    elif mv == 'row':
        # a row of squares with the angle of k slides along itself
        t = tilt(Q[:, 2])
        same = np.abs(t - t[k]) < 0.01
        ang = Q[k, 2] + int(rng.integers(0, 2)) * HALF_PI
        ux, uy = math.cos(ang), math.sin(ang)
        sel = same & (np.abs(-(Q[:, 0] - Q[k, 0]) * uy + (Q[:, 1] - Q[k, 1]) * ux) < 0.3)
        dl = rng.uniform(-0.3, 0.3)
        Q[sel, 0] += dl * ux; Q[sel, 1] += dl * uy
    elif mv == 'ang':
        # every square with the tilt of one tilted square turns about the group's centre
        t = tilt(Q[:, 2])
        tl = np.nonzero(np.abs(t) > 0.01)[0]
        if not len(tl):
            return None, mv
        k = int(tl[np.argmin(d[tl])])
        sel = np.abs(t - t[k]) < 0.01
        a = rng.uniform(-0.021, 0.021)
        c0 = Q[sel, :2].mean(0)
        dx, dy = Q[sel, 0] - c0[0], Q[sel, 1] - c0[1]
        Q[sel, 0] = c0[0] + math.cos(a) * dx - math.sin(a) * dy
        Q[sel, 1] = c0[1] + math.sin(a) * dx + math.cos(a) * dy
        Q[sel, 2] += a
    elif mv == 'arm':
        t = tilt(Q[:, 2])
        up = np.abs(t) < math.radians(1.0)
        tl = np.abs(t) > math.radians(3.0)
        # an upright square that touches a tilted one, nearest to k
        cand = [i for i in np.argsort(d)[:60] if up[i]]
        for i in cand:
            di = np.hypot(Q[:, 0] - Q[i, 0], Q[:, 1] - Q[i, 1])
            nb = np.nonzero(tl & (di < 1.45))[0]
            if len(nb):
                j = nb[np.argmin(di[nb])]
                Q[i, 2] = Q[j, 2]
                break
        else:
            return None, mv
    return Q, mv


def legal(P):
    """Exact repair and squeeze. Returns (P, side) or None."""
    Q, _ = mlp.reclose(P, 0.02)
    if mlp.min_gap(Q) < 2.5e-11:
        return None
    Q, L, _ = mlp.slp(Q, iters=8)
    if mlp.min_gap(Q) < 2.5e-11:
        return None
    return Q, L


def write(out, n, P, tag, sub='raw'):
    """sub = 'raw' for a legal packing; 'softfree' keeps a member as it is (no shift), for a look afterwards."""
    if sub == 'raw':
        P = mlp.normal(P)
    os.makedirs('%s/%s' % (out, sub), exist_ok=True)
    final = '%s/%s/%d-%s.csv' % (out, sub, n, tag)
    tmp = final + '.tmp' 
    with open(tmp, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for k, (x, y, th) in enumerate(P):
            w.writerow([n, k, repr(float(x)), repr(float(y)), repr(float(th))])
    os.replace(tmp, final)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sub'); ap.add_argument('out'); ap.add_argument('--n', type=int, required=True)
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--delta', type=float, default=2e-4); ap.add_argument('--pop', type=int, default=12)
    ap.add_argument('--moves', default='row,ang,jig,clu,twi,blk,arm')
    ap.add_argument('--start', default='best', help='best, or dropK: the held n+K minus K random squares; '
                    'an m in front (mbest, mdrop1) makes a mirror island: every child is made symmetric about the diagonal')
    ap.add_argument('--local', type=int, default=1, help='1 = relax only the squares within 2.5 of the move (about 8 times more children a second)')
    ap.add_argument('--global-every', type=int, default=100, help='children between whole-packing relaxations of the best member')
    ap.add_argument('--try-every', type=int, default=200, help='children between ladder tries on a best member that moved')
    ap.add_argument('--below', type=float, default=15, help='restart from the legal state when the box is this many deltas below it'); ap.add_argument('--maxiter', type=int, default=200)
    ap.add_argument('--kernel', default='c', help='c = the compiled energy and L-BFGS (numpy when cc is missing), numpy = scipy L-BFGS-B on the numpy energy')
    ap.add_argument('--mirror-box', default='settle', help="settle = a mirror island starts just below the box where its seed is "
                    "soft-free; below = it starts just below the legal best, with the overlap that takes")
    ap.add_argument('--restart', type=int, default=3000, help='children with no find before the island starts again from its legal best (0 = never)')
    ap.add_argument('--dry', type=float, default=0, help='seconds with no find after which the island ends (0 = never). 360 is the rule of rounds 8 to 10')
    ap.add_argument('--keep-softfree', type=int, default=0, help='1 = a plain island also writes its soft-free members that did not become legal to OUTDIR/softfree (a mirror island always does)')
    a = ap.parse_args()
    os.makedirs(a.out + '/raw', exist_ok=True)
    n = a.n
    if a.kernel == 'c':
        load_kernel()
    rng = np.random.default_rng(a.seed * 100003 + n)
    P0 = mlp.normal(mlp.load(a.sub, {n})[n])
    best, Lbest = P0, mlp.side(P0)
    L0 = Lbest
    moves = a.moves.split(',')
    cur, Lcur = best, Lbest          # the legal packing the box hangs under (the best, or a drop seed above it)
    sym = a.start.startswith('m')
    st = a.start[1:] if sym else a.start
    if st.startswith('drop'):
        cur = drop_seed(a.sub, n, rng, int(st[4:] or 1)); Lcur = mlp.side(cur)
    legal_known = not sym
    lg = open('%s/soft-%d-%s-%d.log' % (a.out, n, a.start, a.seed), 'a')

    def log(s):
        lg.write(s + '\n'); lg.flush()
    log('start n=%d L=%.12f delta=%g pop=%d moves=%s start=%s' % (n, Lbest, a.delta, a.pop, a.moves, a.start))
    t0 = time.time(); kids = 0; finds = 0; last_try = 0; last_E = math.inf
    mark = 0; mark_finds = 0; restarts = 0          # mark: the child count at the last find or restart
    stats = {m: [0, 0, 0] for m in moves}      # tried, survived, led to a find

    def seed_pop(P, L):
        # the LP returns a packing whose bounding box need not sit at the origin: put it there first
        Q, E = relax(mlp.normal(P), L, a.maxiter)
        return [(E, Q, 'start')]
    box = Lcur - a.delta
    H = 0
    if sym:
        # a mirror island: the seed is made symmetric, overlap-free and as small as it goes first
        src = (0, 1, 2) if st == 'best' else tuple(range(int(st[4:] or 1), int(st[4:] or 1) + 2))
        ms_ = mirror_seed(a.sub, n, src, a.delta, log, Lbest)
        if ms_ is None:
            log('end n=%d no mirror seed' % n); print('n=%d no mirror seed' % n, flush=True); return
        cur, Lcur, H = ms_
        log('mirror island: soft-free at box %.9f, legal best %.9f (%+.6f)' % (Lcur, Lbest, Lcur - Lbest))
        box = Lcur - a.delta
        if a.mirror_box == 'below' and box > Lbest - a.delta:
            # the public GA's way: the island lives below the legal best from the start, with E > 0,
            # and the moves bring E down. The settled seed is scaled into that box.
            box = Lbest - a.delta
            cur = cur.copy(); cur[:, :2] *= box / Lcur; Lcur = box + a.delta
        pop = [sym_relax(cur, box, H, 3000)[::-1] + ('start',)]
        log('mirror island: starts at box %.9f with E %.3e' % (box, pop[0][0]))
    else:
        pop = seed_pop(cur, box)
    t_find = t0                                     # the time of the last find (the start, before the first one)
    while time.time() - t0 < a.seconds and not (a.dry and time.time() - t_find >= a.dry):
        E0, P, _ = pop[int(rng.integers(len(pop)))]
        w = overlap_weight(pop[0][1], box)
        Q, mv = mutate(P, box, w, rng, moves)
        if Q is None:
            continue
        if sym:
            Q = project(Q, P, H)
        # a mirror child differs from its parent in the last bit all over (the symmetrisation rounds), so
        # "changed" needs a tolerance there, and the active set must be symmetric: without both, the
        # symmetrisation moved squares outside the set and the kept energy missed their overlaps
        act = (active_set(P, Q, tol=1e-12, h=H) if sym else active_set(P, Q)) if a.local else None
        if act is not None and act.sum() < 0.6 * n:
            # only the squares near the move relax; the rest of E is unchanged, so the total follows exactly
            e_par = local_energy(P, box, act)
            if sym:
                Q, e_loc = sym_relax(Q, box, H, a.maxiter, act)
            else:
                Q, e_loc = relax_local(Q, box, act, a.maxiter)
            E = E0 - e_par + e_loc
        elif sym:
            Q, E = sym_relax(Q, box, H, a.maxiter)
        else:
            Q, E = relax(Q, box, a.maxiter)
        kids += 1; stats[mv][0] += 1
        if finds > mark_finds:
            mark, mark_finds = kids, finds
        # a mirror island works above or below its start for long stretches: there a box drop counts as
        # progress too, and it gets five times the children before it starts again from its anchor
        if a.restart and kids - mark >= a.restart * (5 if sym else 1):
            # no find for a.restart children: the island is stalled far below its legal side, so start again
            mark = kids; restarts += 1; last_E = math.inf
            if not sym:
                cur, Lcur = best, Lbest
            box = Lcur - a.delta
            pop = [sym_relax(cur, box, H, a.maxiter)[::-1] + ('start',)] if sym else seed_pop(cur, box)
            log('restart %d t %.0f kids %d box %.9f best %.9f' % (restarts, time.time() - t0, kids, box, Lbest))
            continue
        if a.local and kids % a.global_every == 0:
            # let the stress of the best member spread
            Qg, Eg = sym_relax(pop[0][1], box, H, a.maxiter) if sym else relax(pop[0][1], box, a.maxiter)
            if Eg < pop[0][0]:
                pop[0] = (Eg, Qg, pop[0][2])
        dup = any(abs(E - e) <= 1e-3 * e for e, _, _ in pop) and E >= pop[0][0]    # a copy of a member adds nothing
        if not dup and (len(pop) < a.pop or E < pop[-1][0]):
            pop.append((E, Q, mv)); pop.sort(key=lambda z: z[0]); pop = pop[:a.pop]
            stats[mv][1] += 1
        if kids % 50 == 0:
            log('t %.0f kids %d box %.9f E %s' % (time.time() - t0, kids, box, ' '.join('%.1e' % p[0] for p in pop[:4])))
        if kids - last_try >= a.try_every and pop[0][0] < 0.97 * last_E:
            # the best member moved: see whether it is legal below the best in a box a little above its own
            last_try, last_E = kids, pop[0][0]
            lad = ladder(pop[0][1], box, Lbest)
            if lad is not None:
                r = legal(lad[0])
                best, Lbest = r if (r is not None and r[1] < lad[1]) else lad
                if not sym:
                    cur, Lcur = best, Lbest; legal_known = True
                finds += 1; stats.get(pop[0][2], [0, 0, 0])[2] += 1; t_find = time.time()
                write(a.out, n, best, '%s-%d' % (a.start, a.seed))
                log('FIND t %.0f kids %d move %s box %.9f L %.12f (start %.12f, gain of score %.3e) ladder' % (
                    time.time() - t0, kids, pop[0][2], box, Lbest, L0, (L0 - Lbest) / math.sqrt(n)))
        if pop[0][0] < 1e-10 * n:
            # soft-free at this box: try the exact repair, then drop the box again
            E, Q, mv = pop[0]
            if sym:
                # the kept energy of a mirror member is a sum of local updates: count it afresh before the box moves
                Ef = total_energy(Q, box)
                if Ef >= 1e-10 * n:
                    log('kept energy %.3e was low, fresh %.3e: not soft-free' % (E, Ef))
                    pop[0] = (Ef, Q, mv); pop.sort(key=lambda z: z[0])
                    continue
                cur, Lcur = Q, box          # the island's own anchor: its last soft-free symmetric state
            lad = ladder(Q, box, Lbest)
            if lad is not None:
                R, LR = lad; okR = True
            else:
                R, LR = mlp.reclose(Q, 0.02)
                okR = mlp.min_gap(R) >= 2.5e-11
            if not sym and okR and (LR < Lcur or not legal_known):
                cur, Lcur = R, LR; legal_known = True
            if okR and LR < Lbest - 1e-9:
                r = legal(R)
                if r is not None and r[1] < LR:
                    R, LR = r
                best, Lbest = R, LR
                if not sym:
                    cur, Lcur = best, Lbest
                finds += 1; stats.get(mv, [0, 0, 0])[2] += 1; t_find = time.time()
                write(a.out, n, best, '%s-%d' % (a.start, a.seed))
                log('FIND t %.0f kids %d move %s box %.9f L %.12f (start %.12f, gain of score %.3e)' % (
                    time.time() - t0, kids, mv, box, Lbest, L0, (L0 - Lbest) / math.sqrt(n)))
            elif box < Lbest and (sym or a.keep_softfree):
                # soft-free below the legal best and no legal packing came out of it: keep the member, with
                # what the exact gap test and a fresh energy say about it (not in raw/: it is not a result)
                h_ = mlp.half(Q[:, 2])
                wall = max(float((h_ - Q[:, :2].min(1)).max()), float((Q[:, :2].max(1) + h_ - box).max()))
                write(a.out, n, Q, '%s-%d-box%.6f' % (a.start, a.seed, box), 'softfree')
                log('SOFTFREE-ILLEGAL t %.0f kids %d box %.9f (%.6f below best) E kept %.3e fresh %.3e min_gap %.3e wall %.3e ladder %s' % (
                    time.time() - t0, kids, box, Lbest - box, E, total_energy(Q, box), mlp.min_gap(Q), wall,
                    'none' if lad is None else 'side %.9f' % lad[1]))
            # far above the last soft-free energy the box can drop faster
            box -= a.delta * (4 if E < 1e-12 * n else 1)
            if sym:
                mark = kids
            log('box t %.0f kids %d box %.9f legal %.9f best %.9f' % (time.time() - t0, kids, box, Lcur, Lbest))
            if legal_known and box < Lcur - a.below * a.delta:   # far below anything legal: start again from the legal state
                box = Lcur - a.delta
                pop = seed_pop(cur, box)
            else:
                pop = [(sym_relax(q, box, H, a.maxiter) if sym else relax(q, box, a.maxiter))[::-1] + (m,)
                       for _, q, m in pop[:max(3, a.pop // 3)]]
                pop.sort(key=lambda z: z[0])
    log('end n=%d kids %d finds %d restarts %d L %.12f -> %.12f gain %.3e stats %s seconds %.0f' % (
        n, kids, finds, restarts, L0, Lbest, (L0 - Lbest) / math.sqrt(n), stats, time.time() - t0))
    print('n=%d kids %d finds %d L %.12f -> %.12f gain %.3e %s' % (n, kids, finds, L0, Lbest, (L0 - Lbest) / math.sqrt(n), stats), flush=True)


if __name__ == '__main__':
    main()
