"""Small statistical helpers.

No result here is a causal estimate. Callers name the sampling unit and the
assumption. Non-significance is not evidence of absence.
"""
from __future__ import annotations

import math
import random
from collections import Counter


Z95 = 1.959963984540054


def wilson_interval(successes: int, n: int, z: float = Z95) -> dict:
    """Wilson score interval for a binomial proportion.

    Returns an empty interval when n is 0. The point estimate is successes/n.
    """
    if n < 0 or successes < 0 or successes > n:
        raise ValueError(f"invalid binomial counts k={successes} n={n}")
    if n == 0:
        return {"k": 0, "n": 0, "p": None, "low": None, "high": None, "method": "wilson"}
    p = successes / n
    z2 = z * z
    den = 1.0 + z2 / n
    centre = (p + z2 / (2.0 * n)) / den
    half = z * math.sqrt((p * (1.0 - p) / n) + z2 / (4.0 * n * n)) / den
    return {
        "k": successes,
        "n": n,
        "p": p,
        "low": max(0.0, centre - half),
        "high": min(1.0, centre + half),
        "method": "wilson",
    }


def hhi(labels: list[str]) -> float | None:
    """Herfindahl-Hirschman index on a multiset of labels. Empty input is undefined."""
    vals = [x for x in labels if x]
    if not vals:
        return None
    counts = Counter(vals)
    n = sum(counts.values())
    return sum((v / n) ** 2 for v in counts.values())


def jaccard(a, b) -> float | None:
    left = {x for x in a if x}
    right = {x for x in b if x}
    if not left and not right:
        return None
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def kendall_tau_a(rank_a: dict[str, int], rank_b: dict[str, int]) -> dict:
    """Kendall tau-a on the intersection of two rankings.

    Undefined when fewer than two items appear in both lists. This is the
    conjoint overlap only. Items present in just one list do not enter.
    """
    shared = [k for k in rank_a if k in rank_b]
    pairs = 0
    concordant = 0
    discordant = 0
    ties = 0
    for i in range(len(shared)):
        for j in range(i + 1, len(shared)):
            a = rank_a[shared[i]] - rank_a[shared[j]]
            b = rank_b[shared[i]] - rank_b[shared[j]]
            pairs += 1
            prod = a * b
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
            else:
                ties += 1
    decided = concordant + discordant
    tau = None if decided == 0 else (concordant - discordant) / decided
    return {
        "n_shared": len(shared),
        "pairs": pairs,
        "concordant": concordant,
        "discordant": discordant,
        "ties": ties,
        "tau_a": tau,
        "defined": decided > 0 and len(shared) >= 2,
    }


def rbo(list1: list[str], list2: list[str], p: float = 0.9) -> float | None:
    """Extrapolated rank-biased overlap (Webber, Moffat, Zobel 2010).

    Identical rankings score 1. Disjoint rankings score 0. A two-item reversal
    scores p. The parameter p is the weight on depth; 0.9 puts most of the
    weight on the top of the list. Unequal lengths are handled by freezing the
    shorter prefix and extrapolating the last overlap ratio.
    """
    if not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    if not list1 and not list2:
        return None
    if not list1 or not list2:
        return 0.0
    short, long = (list1, list2) if len(list1) <= len(list2) else (list2, list1)
    seen_s: set[str] = set()
    seen_l: set[str] = set()
    overlap = 0
    weighted = 0.0
    for d in range(1, len(long) + 1):
        if d <= len(short):
            seen_s.add(short[d - 1])
        seen_l.add(long[d - 1])
        overlap = len(seen_s & seen_l)
        weighted += (overlap / d) * (p ** d)
    extrapolated = (overlap / len(long)) * (p ** len(long))
    return ((1.0 - p) / p) * weighted + extrapolated


def holm(pvalues: list[tuple[str, float]]) -> list[dict]:
    """Holm step-down adjusted p-values. Names travel with the values."""
    m = len(pvalues)
    ordered = sorted(pvalues, key=lambda item: item[1])
    running = 0.0
    raw_adj = []
    for i, (name, p) in enumerate(ordered):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        raw_adj.append((name, p, running))
    by_name = {name: (p, adj) for name, p, adj in raw_adj}
    return [
        {"name": name, "p": by_name[name][0], "p_holm": by_name[name][1]}
        for name, _ in pvalues
    ]


def benjamini_hochberg(pvalues: list[tuple[str, float]]) -> list[dict]:
    """Benjamini-Hochberg FDR adjustment, monotone from the largest p."""
    m = len(pvalues)
    ordered = sorted(pvalues, key=lambda item: item[1])
    adj_desc = []
    running = 1.0
    for i in range(m - 1, -1, -1):
        name, p = ordered[i]
        rank = i + 1
        val = min(running, min(1.0, p * m / rank))
        running = val
        adj_desc.append((name, p, val))
    by_name = {name: (p, adj) for name, p, adj in adj_desc}
    return [
        {"name": name, "p": by_name[name][0], "p_bh": by_name[name][1]}
        for name, _ in pvalues
    ]


def percentile_ci(samples: list[float], alpha: float = 0.05) -> dict:
    vals = sorted(x for x in samples if x is not None and not math.isnan(x))
    if not vals:
        return {"low": None, "high": None, "n": 0}
    lo_i = int(math.floor((alpha / 2) * (len(vals) - 1)))
    hi_i = int(math.ceil((1 - alpha / 2) * (len(vals) - 1)))
    return {"low": vals[lo_i], "high": vals[hi_i], "n": len(vals)}


def cluster_bootstrap(
    clusters: list,
    statistic,
    *,
    n_boot: int = 2000,
    seed: int = 20261028,
    alpha: float = 0.05,
) -> dict:
    """Resample whole clusters with replacement and take a percentile interval.

    With one cluster the interval collapses to the point. Callers must not
    describe that as precision.
    """
    point = statistic(clusters)
    if len(clusters) == 0:
        return {"point": None, "low": None, "high": None, "n_clusters": 0, "n_boot": 0}
    rng = random.Random(seed)
    draws = []
    m = len(clusters)
    for _ in range(n_boot):
        sample = [clusters[rng.randrange(m)] for _ in range(m)]
        value = statistic(sample)
        if value is not None:
            draws.append(float(value))
    ci = percentile_ci(draws, alpha)
    return {
        "point": None if point is None else float(point),
        "low": ci["low"],
        "high": ci["high"],
        "n_clusters": m,
        "n_boot": len(draws),
        "degenerate": m < 2,
    }


def permutation_pvalue(
    group_a: list,
    group_b: list,
    statistic,
    *,
    n_perm: int = 4999,
    seed: int = 20261028,
) -> dict:
    """Two-sided permutation p-value for statistic(A) - statistic(B).

    The null is that the group labels are exchangeable. If the groups are
    single chats, that null is not a population model of bots. The returned
    p-value is valid only for the exchangeability claim the caller states.
    """
    if not group_a or not group_b:
        return {"diff": None, "p": None, "n_perm": 0, "n_a": len(group_a), "n_b": len(group_b)}
    obs_a = statistic(group_a)
    obs_b = statistic(group_b)
    if obs_a is None or obs_b is None:
        return {"diff": None, "p": None, "n_perm": 0, "n_a": len(group_a), "n_b": len(group_b)}
    observed = float(obs_a) - float(obs_b)
    pool = list(group_a) + list(group_b)
    n_a = len(group_a)
    rng = random.Random(seed)
    extreme = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        diff = float(statistic(pool[:n_a])) - float(statistic(pool[n_a:]))
        if abs(diff) >= abs(observed) - 1e-12:
            extreme += 1
    p = (extreme + 1) / (n_perm + 1)
    return {
        "diff": observed,
        "stat_a": float(obs_a),
        "stat_b": float(obs_b),
        "p": p,
        "n_perm": n_perm,
        "n_a": n_a,
        "n_b": len(group_b),
    }


def within_list_permutation(
    lists: list[list[bool]],
    *,
    n_perm: int = 4999,
    seed: int = 20261028,
) -> dict:
    """Sharp null: within each list, the True label is equally likely on any row.

    `lists` holds, for each informative run, a boolean per displayed row, True
    when that row has the attribute (for example, it is the cheapest). The
    observed score is the number of lists whose first row is True. The
    permutation shuffles each list. Lists with no variation, or shorter than
    2, must be omitted by the caller.
    """
    usable = [row for row in lists if len(row) >= 2 and any(row) and not all(row)]
    if not usable:
        return {"k": 0, "n_lists": 0, "p_one_sided": None, "null_mean": None, "n_perm": 0}
    observed = sum(1 for row in usable if row[0])
    rng = random.Random(seed)
    extreme = 0
    null_total = 0.0
    for _ in range(n_perm):
        score = 0
        for row in usable:
            score += 1 if row[rng.randrange(len(row))] else 0
        null_total += score
        if score >= observed:
            extreme += 1
    p = (extreme + 1) / (n_perm + 1)
    return {
        "k": observed,
        "n_lists": len(usable),
        "p_one_sided": p,
        "null_mean": null_total / n_perm,
        "n_perm": n_perm,
        "alternative": "rank-1 carries the attribute more often than a shuffle of the shown rows",
    }
