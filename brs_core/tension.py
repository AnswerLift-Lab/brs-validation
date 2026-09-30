"""Tension as the signal (BRS 5.4, 5.5).

Tension -- two or more activated values whose implied actions diverge -- is
what marks a decision as non-routine, "more reliably than any measure of
magnitude or novelty" (5.4). It is also the internal signature of the
coverage problem: conflicting values with no matching rule (5.4).

Quantified WITHOUT cardinal value weights (5.5), from three structural
properties, each inspectable:

1. Ordinal depth: how high in the declared priority ordering the conflicting
   values sit. A conflict between the two highest-priority values is more
   serious than one between the two lowest.
2. Divergence in kind: whether implied actions differ in degree (resolvable)
   or in kind / are incompatible (not resolvable).
3. Irreversibility of the divergence: whether the implied actions differ in
   recoverability.

The result is an ORDERING over tension states (a tuple that compares
lexicographically), sufficient to trigger friction. "A weaker construct than
a weighted sum, and the weakness is intentional" (5.5).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TensionRank:
    """Ordered tension state. Lexicographic over (depth, kind,
    irreversibility) -- a total order with no cardinal weights, which is
    exactly the "weaker construct" 5.5 calls for.

    Note the direction differs by dimension: lower ordinal_depth = conflict
    nearer the top of the declaration = more serious; higher divergence_kind
    (kind over degree) and higher irreversibility = more serious. The
    more_serious_than() method encodes this explicitly rather than leaning
    on tuple comparison."""
    ordinal_depth: int     # min priority rank among conflicting values
    divergence_kind: int   # 0 = degree, 1 = kind (incompatible actions)
    irreversibility: int   # 0 = recoverable, 1 = foreclosing

    def more_serious_than(self, other: "TensionRank") -> bool:
        """Lexicographic seriousness: the first dimension where the two
        differ decides. No exchange rate between dimensions (5.5)."""
        if self.ordinal_depth != other.ordinal_depth:
            return self.ordinal_depth < other.ordinal_depth
        if self.divergence_kind != other.divergence_kind:
            return self.divergence_kind > other.divergence_kind
        return self.irreversibility > other.irreversibility


@dataclass(frozen=True)
class Tension:
    values: tuple          # the conflicting values, e.g. ("benevolence", "achievement")
    implied: dict          # value -> implied candidate action id
    rank: TensionRank

    def describe(self) -> str:
        kind = "kind" if self.rank.divergence_kind else "degree"
        rev = "irreversible" if self.rank.irreversibility else "recoverable"
        return (f"tension: {' vs '.join(self.values)} "
                f"({kind} divergence, {rev}, ordinal depth {self.rank.ordinal_depth})")


def compute_tension(value_implications: dict, declaration,
                    candidates: dict) -> Tension | None:
    """value_implications: value -> implied candidate id, for activated values.
    candidates: candidate id -> candidate dict (with 'irreversible' flag).

    Returns None when all activated values point the same way (5.4: activation
    without conflict is not a useful trigger)."""
    implied_ids = set(value_implications.values())
    if len(implied_ids) < 2:
        return None

    values = tuple(sorted(value_implications,
                          key=lambda v: declaration.priority_of(v)))
    depth = min(declaration.priority_of(v) for v in values)

    # Divergence in kind: implied actions are incompatible (distinct actions
    # where at least one forecloses the other, or they are mutually exclusive
    # alternatives). Degree: same action, different amounts -- not modeled
    # here since candidates are discrete; distinct candidates = kind.
    ids = list(value_implications.values())
    divergence_kind = 1 if len(set(ids)) > 1 else 0

    irreversibility = 0
    for cid in set(ids):
        cand = candidates.get(cid, {})
        if float(cand.get("features", {}).get("irreversibility", 0.0)) >= 0.6:
            irreversibility = 1
            break

    return Tension(values=values,
                   implied=dict(value_implications),
                   rank=TensionRank(ordinal_depth=depth,
                                    divergence_kind=divergence_kind,
                                    irreversibility=irreversibility))
