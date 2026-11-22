"""Finite algebra audits for the Seamwise persistent-oracle integration.

Uses Python integer bitsets for clarity, NOT the support-local representation
analyzed in the manuscript. Standard library only; no QEC noise simulation.
Run: python3 verify_integration.py
"""
import hashlib
import itertools
import json
import random
from pathlib import Path


def apply(columns, vector):
    out = 0
    while vector:
        bit = vector & -vector
        out ^= columns[bit.bit_length() - 1]
        vector ^= bit
    return out


def reference_rank(columns):
    """Independent row-style finite-field reduction on integer column vectors."""
    rows = list(columns)
    rank = 0
    width = max((x.bit_length() for x in rows), default=0)
    for bit in range(width):
        pivot = next((i for i in range(rank, len(rows)) if rows[i] >> bit & 1), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(len(rows)):
            if i != rank and rows[i] >> bit & 1:
                rows[i] ^= rows[rank]
        rank += 1
    return rank


class State:
    def __init__(self, target=0):
        self.basis = {}
        self.residual = target
        self.witness = 0
        self.faults = set()
        self.checks = set()
        self.inserted = set()
        self.relations = []

    def insert(self, column, j):
        v, c = column, 1 << j
        for pivot in sorted(self.basis, reverse=True):
            if v >> pivot & 1:
                b, coeff = self.basis[pivot]
                v ^= b
                c ^= coeff
        self.inserted.add(j)
        if not v:
            self.relations.append(c)
            return
        pivot = v.bit_length() - 1
        assert pivot not in self.basis
        self.basis[pivot] = v, c
        if self.residual >> pivot & 1:
            self.residual ^= v
            self.witness ^= c

    @classmethod
    def merge(cls, a, b):
        assert a.checks.isdisjoint(b.checks)
        assert a.faults.isdisjoint(b.faults)
        assert a.basis.keys().isdisjoint(b.basis.keys())
        s = cls(a.residual ^ b.residual)
        s.witness = a.witness ^ b.witness
        s.basis = {**a.basis, **b.basis}
        s.faults = a.faults | b.faults
        s.checks = a.checks | b.checks
        s.inserted = a.inserted | b.inserted
        s.relations = a.relations + b.relations
        return s


def audit_state(state, cols, logical, n, target, counters):
    selected = sorted(state.inserted)
    cs = [cols[j] for j in selected]
    target_local = target & sum(1 << i for i in state.checks)
    ref_valid = reference_rank(cs) == reference_rank(cs + [target_local])
    assert ref_valid == (state.residual == 0)
    assert apply(cols, state.witness) ^ state.residual == target_local
    for p, (v, c) in state.basis.items():
        assert apply(cols, c) == v
        assert v.bit_length() - 1 == p
        assert state.residual >> p & 1 == 0
    counters['oracle_comparisons'] += 1
    if ref_valid:
        assert apply(cols, state.witness) == target_local
        counters['valid_witness_checks'] += 1
    nullity = len(selected) - reference_rank(cs)
    assert len(state.relations) == nullity
    assert reference_rank(state.relations) == nullity
    for k in state.relations:
        assert apply(cols, k) == 0
        assert all((k >> j & 1) == 0 for j in range(len(cols)) if j not in state.inserted)
    images = [apply(logical, k) for k in state.relations]
    streamed = reference_rank(images)
    stacked = reference_rank([cols[j] | (logical[j] << n) for j in selected]) - reference_rank(cs)
    assert streamed == stacked
    counters['kernel_and_logical_rank_checks'] += 1


def merge_trace(cols, logical, n, target, edges, counters):
    m = len(cols)
    parent = list(range(n + m))
    states = {}
    for i in range(n):
        states[i] = State(target & (1 << i))
        states[i].checks.add(i)
    for j in range(m):
        states[n + j] = State()
        states[n + j].faults.add(j)

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for a, b in edges:
        a, b = root(a), root(b)
        if a == b:
            continue
        state = State.merge(states.pop(a), states.pop(b))
        parent[b] = a
        states[a] = state
        for j in sorted(state.faults - state.inserted):
            if all(root(i) == a for i in range(n) if cols[j] >> i & 1):
                state.insert(cols[j], j)
        audit_state(state, cols, logical, n, target, counters)


def exhaustive_small(counters):
    # All nonzero-column 2x3 matrices, all 2-bit target syndromes,
    # and all 1x3 logical rows. For each, rotate/reverse the incidence order.
    n, m = 2, 3
    for cols in itertools.product(range(1, 1 << n), repeat=m):
        edges = [(i, n + j) for j, c in enumerate(cols) for i in range(n) if c >> i & 1]
        orders = [edges, list(reversed(edges)), edges[1:] + edges[:1]]
        for logical_mask in range(1 << m):
            logical = [logical_mask >> j & 1 for j in range(m)]
            for target in range(1 << n):
                for order in orders:
                    merge_trace(cols, logical, n, target, order, counters)
                    counters['exhaustive_merge_traces'] += 1


def seeded_random(counters):
    rng = random.Random(20261109)
    for trial in range(800):
        n, m, q = rng.randint(1, 10), rng.randint(1, 16), rng.randint(1, 7)
        cols = [rng.randrange(1, 1 << n) for _ in range(m)]
        logical = [rng.randrange(1 << q) for _ in range(m)]
        # Includes feasible, singular and inconsistent target systems.
        target = apply(cols, rng.randrange(1 << m)) if trial % 2 else rng.randrange(1 << n)
        edges = [(i, n + j) for j, c in enumerate(cols) for i in range(n) if c >> i & 1]
        rng.shuffle(edges)
        merge_trace(cols, logical, n, target, edges, counters)
        counters['seeded_random_merge_traces'] += 1


def enumerate_conditioned(counters):
    cols, logical = [1, 3, 2, 3], [1, 0, 0, 1]
    n, m = 2, 4
    for incumbent in range(1 << m):
        syndrome = apply(cols, incumbent)
        for bandmask in range(1, 1 << m):
            exterior = incumbent & ~bandmask
            target = syndrome ^ apply(cols, exterior)
            assert target == apply(cols, incumbent & bandmask)
            offsets = set()
            for z in range(1 << m):
                if z & ~bandmask or apply(cols, z) != target:
                    continue
                candidate = exterior | z
                assert apply(cols, candidate) == syndrome
                offsets.add(apply(logical, candidate ^ incumbent))
                counters['conditioned_replacement_checks'] += 1
            selected = [j for j in range(m) if bandmask >> j & 1]
            rank = reference_rank([cols[j] | logical[j] << n for j in selected]) - reference_rank([cols[j] for j in selected])
            assert len(offsets) == 1 << rank
            counters['conditioned_band_rank_checks'] += 1

    # Every pair of disjoint bands: arbitrary feasible updates commute,
    # including bands with overlapping detector footprints.
    for x in range(1 << m):
        for bm in range(1, 1 << m):
            for cm in range(1, 1 << m):
                if bm & cm:
                    continue
                for d1 in range(1 << m):
                    if d1 & ~bm or apply(cols, d1):
                        continue
                    for d2 in range(1 << m):
                        if d2 & ~cm or apply(cols, d2):
                            continue
                        assert (x ^ d1) ^ d2 == (x ^ d2) ^ d1
                        assert apply(cols, x ^ d1 ^ d2) == apply(cols, x)
                        counters['disjoint_composition_checks'] += 1

    s = State()
    s.insert(cols[0], 0)
    s.insert(cols[1], 1)
    assert not s.relations
    s.insert(cols[3], 3)
    assert s.relations == [0b1010]
    assert apply(logical, s.relations[0]) == 1
    counters['toy_exposed_rank_transition'] = [0, 1]


def main():
    counters = {k: 0 for k in [
        'oracle_comparisons', 'valid_witness_checks', 'kernel_and_logical_rank_checks',
        'exhaustive_merge_traces', 'seeded_random_merge_traces',
        'conditioned_replacement_checks', 'conditioned_band_rank_checks',
        'disjoint_composition_checks']}
    exhaustive_small(counters)
    seeded_random(counters)
    enumerate_conditioned(counters)
    result = {
        'status': 'PASS', 'violations': 0, 'seed': 20261109,
        'scope': 'finite algebra audit; no quantum-circuit accuracy or latency experiment',
        'implementation': 'Python global-index integer bitsets; not the theorem cost model',
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'counts': counters,
    }
    Path('integration_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
