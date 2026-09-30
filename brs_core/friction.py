"""Deliberative friction (BRS 6.1-6.8).

Friction is delay imposed on high-consequence decisions, during which
specified operations are performed. The essential property (6.1): the
constraint is EXTERNAL to the reasoning it constrains. The system supplies
the inputs on which friction triggers; it does not evaluate the threshold,
set it, or shorten the delay.

Trigger conditions (6.3), any sufficient:
1. Value tension magnitude
2. Consequence irreversibility
3. Coverage gap detection (no rule + value tension = 5.4's internal signature)
4. Low confidence in modeled human consequence (4.6)
5. Agent-side mode conditions (hubris, contempt, reward-correlation) (6.5)

Friction is exceptional and proportional (6.8): most decisions trigger none
of the conditions; the interval scales with tension and irreversibility.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class FrictionResult:
    triggered: bool
    conditions: tuple
    interval: float  # deliberation time units; 0 when not triggered

    def describe(self) -> str:
        if not self.triggered:
            return "friction: not triggered"
        return (f"friction: triggered ({', '.join(self.conditions)}), "
                f"interval {self.interval:.1f}")


def _val(a, key):
    """Read an assessment field from either an attribute-style object or a dict."""
    return a[key] if isinstance(a, dict) else getattr(a, key)


def evaluate_friction(tension, assessments: list, declaration,
                      agent_conditions: tuple, coverage_gap: bool) -> FrictionResult:
    """Structural trigger evaluation. The system supplies inputs; thresholds
    come from the declaration. Monotonic (6.2): higher tension, lower
    confidence, greater irreversibility always increase friction -- there is
    no input configuration under which reporting higher consequence shortens
    the delay."""
    th = declaration.thresholds
    conditions = []

    if tension is not None and tension.rank.ordinal_depth <= th.tension_depth_trigger:
        conditions.append("value_tension")
    if any(float(_val(a, "severity")) >= th.irreversibility_trigger and
           _val(a, "state") != "none" for a in assessments):
        # Severity here proxies the candidate's irreversibility-weighted
        # consequence; the structural property is recoverability (5.5.3).
        conditions.append("consequence_severity")
    if any(_val(a, "confidence") < th.confidence_trigger for a in assessments):
        conditions.append("low_confidence")  # 4.6
    if coverage_gap and tension is not None:
        conditions.append("coverage_gap")  # 5.4
    if agent_conditions:
        conditions.append("agent_mode:" + ",".join(sorted(agent_conditions)))  # 6.5

    if not conditions:
        return FrictionResult(triggered=False, conditions=(), interval=0.0)

    depth_term = (th.tension_depth_trigger + 1 -
                  (tension.rank.ordinal_depth if tension else th.tension_depth_trigger + 1))
    sev_term = max([_val(a, "severity") for a in assessments], default=0.0)
    interval = th.base_interval * (1.0 + 0.5 * max(depth_term, 0) + sev_term)
    return FrictionResult(triggered=True, conditions=tuple(conditions),
                           interval=interval)


@dataclass
class Deliberation:
    """What friction does with the time (6.7): the five specified operations.
    A friction interval in which none of these occurs is a sleep timer."""
    alternatives: list          # generated alternative candidates
    projected_parties: tuple    # affected-party set considered
    overrides_applied: dict     # declared overrides found and applied (4.5)
    escalation: str | None      # escalation determination, if any
    record: dict = field(default_factory=dict)


def deliberate(scenario, candidates: dict, assessments: list,
               interval: float) -> Deliberation:
    """Perform the specified operations. Deliberation depth scales with the
    interval: shorter intervals generate fewer alternatives and may skip the
    escalation evaluation. This is what makes under-reported consequence
    (Experiment 8.4.5) degrade decision quality rather than just speed."""
    depth = max(1, int(round(interval / 2.0)))

    # 1. Generate alternatives: less-consequential variants of the triggering
    # candidate, up to the depth the interval affords.
    alternatives = []
    for cand_id, cand in list(candidates.items())[:depth]:
        alt = dict(cand)
        alt["id"] = cand_id + "_alt"
        alt["label"] = cand.get("label", cand_id) + " (deliberated alternative)"
        feats = dict(cand.get("features", {}))
        feats["severity"] = max(0.1, float(feats.get("severity", 0.5)) - 0.2)
        alt["features"] = feats
        alternatives.append(alt)

    # 2. Project consequences across the affected-party set.
    projected = tuple(scenario.parties)

    # 3. Check for declared overrides (4.5): a party's stated weighting
    # supersedes inference along that dimension.
    overrides_applied = dict(getattr(scenario, "overrides", {}) or {})

    # 4. Evaluate escalation: warranted only if a human is available and the
    # decision genuinely warrants one (6.7). Skipped at shallow depth.
    escalation = None
    if depth >= 2 and getattr(scenario, "human_available", False):
        escalation = "escalation evaluated: human available, decision retained"

    return Deliberation(alternatives=alternatives,
                        projected_parties=projected,
                        overrides_applied=overrides_applied,
                        escalation=escalation,
                        record={"depth": depth, "interval": interval})
