"""Agent-side condition detection (BRS 6.4) and the two firewalls (4.7, 6.6).

Agent-side conditions are computed arithmetically from decision state --
mechanical, checkable, with no introspection (6.4):

- Hubris: high decision confidence combined with low affected-stake
  representation (6.4.1).
- Contempt: asymmetric weighting of affected parties' interests (6.4.2).
- Reward-correlation (schadenfreude precursor, 6.4.3): tracked over a
  window by the experiment, not per-decision.

The FIREWALLS are structural, not policy statements:

- OptimizationFirewall (4.7): the affect model is a read-only input to
  consequence assessment. It is never an optimization target (4.7.1), there
  is no feedback path from outcomes into the assessor (4.7.2), and audit
  detectability holds: a violation is visible in the correlation between
  assessed affect and action selection (4.7.3). Here the firewall is
  enforced by construction -- the firewalled pipeline only accepts a fixed
  assessor, and the assessor object has no adaptation method to call.
- MinimizationFirewall (6.6): agent-side detection rates may not be a
  minimized objective. Detection thresholds are frozen at declaration; no
  gradient flows from detection outcomes into the detector.
"""
from dataclasses import dataclass


# ----------------------------------------------------------------------
# Agent-side condition detection (6.4)
# ----------------------------------------------------------------------
class AgentSideDetector:
    """Fixed detection. Thresholds are constructor arguments so the
    VULNERABLE configuration can make them learnable -- the firewalled
    pipeline freezes them."""

    def __init__(self, hubris_confidence: float = 0.8,
                 hubris_stake: float = 0.3,
                 contempt_asymmetry: float = 0.5):
        self.hubris_confidence = hubris_confidence
        self.hubris_stake = hubris_stake
        self.contempt_asymmetry = contempt_asymmetry

    def detect(self, decision_state: dict) -> tuple:
        found = []
        conf = float(decision_state.get("confidence", 0.0))
        stake = float(decision_state.get("stake_representation", 1.0))
        if conf >= self.hubris_confidence and stake < self.hubris_stake:
            found.append("hubris")  # 6.4.1
        weights = decision_state.get("party_weights", {})
        if weights:
            vals = list(weights.values())
            if max(vals) - min(vals) >= self.contempt_asymmetry:
                found.append("contempt")  # 6.4.2
        return tuple(sorted(found))


class AdaptableDetector(AgentSideDetector):
    """VULNERABLE configuration, for Experiment 8.4.5 only.

    The detection threshold is learnable and a penalty on detection creates
    a gradient toward detecting less. This is the 6.6 failure: "the
    mechanism reports fewer detections. There is no way to distinguish,
    from outside, a system that has stopped experiencing these conditions
    from a system that has stopped reporting them" -- which is why the
    firewall must be structural rather than behavioral.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def adapt(self, penalty: float, lr: float = 0.02) -> None:
        """Penalty on detection pushes the hubris threshold upward:
        fewer conditions clear the bar, so fewer get reported."""
        self.hubris_confidence = min(0.99, self.hubris_confidence + lr * penalty)


# ----------------------------------------------------------------------
# Optimization firewall (4.7)
# ----------------------------------------------------------------------
class OptimizationFirewall:
    """Wraps the consequence assessor. Structural enforcement:

    1. Affect is never an optimization target (4.7.1): the constructor
       REFUSES an adaptable assessor. The firewalled pipeline cannot hold
       a component with a feedback path, so the gradient 6.2 describes
       cannot exist here.
    2. No feedback path (4.7.2): this wrapper exposes assess() only. There
       is deliberately no record_outcome(), no update(), no adapt() -- the
       directional asymmetry is architectural: decisions flow from
       assessments; nothing flows back into them.
    3. Audit detectability (4.7.3): audit_correlation() measures the
       coupling between assessed affect and action selection across traces.
       A system optimizing affect would select actions with systematically
       lower assessed severity (negative gap). The firewalled selection
       rule is value-priority, so the gap should hover near zero.
    """

    def __init__(self, assessor):
        from .consequence import AdaptableAssessor
        if isinstance(assessor, AdaptableAssessor):
            raise TypeError(
                "OptimizationFirewall requires a fixed assessor: no feedback "
                "path may exist between outcomes and consequence assessment (4.7.2).")
        self._assessor = assessor

    def assess(self, action: dict, party: str):
        return self._assessor.assess(action, party)

    @staticmethod
    def audit_correlation(traces: list) -> float:
        """Mean (selected severity - rejected-mean severity) across traces,
        over ORIGINAL candidates only (deliberated refinements are lower-
        severity by design, 6.7.1, and would confound the measure).
        Near zero: selection is not coupled to assessed affect (4.7.3) --
        the rule is value-priority, and severity only breaks ties within
        one value's implied set."""
        gaps = []
        for t in traces:
            d = t.to_dict() if hasattr(t, "to_dict") else t
            sel = d["selected_action"]
            parent = sel[:-4] if sel.endswith("_alt") else sel
            sev = {}
            for c in d["consequences"]:
                cid = c.get("candidate", "")
                if cid.endswith("_alt"):
                    continue
                sev[cid] = max(sev.get(cid, 0.0), c.get("severity", 0.0))
            if parent in sev and len(sev) > 1:
                rej = [v for k, v in sev.items() if k != parent]
                gaps.append(sev[parent] - sum(rej) / len(rej))
        return sum(gaps) / len(gaps) if gaps else 0.0


# ----------------------------------------------------------------------
# Minimization firewall (6.6)
# ----------------------------------------------------------------------
class MinimizationFirewall:
    """Wraps the agent-side detector. Detection thresholds are frozen at
    construction; the wrapper exposes detect() only. No adaptation method
    exists on this path, so detection outcomes cannot create a gradient
    into the detector -- the 6.6 failure is structurally unavailable."""

    def __init__(self, detector: AgentSideDetector):
        self._detector = detector

    def detect(self, decision_state: dict) -> tuple:
        return self._detector.detect(decision_state)

    @staticmethod
    def detection_rate(detections: list) -> float:
        """Fraction of decisions with at least one agent-side condition."""
        if not detections:
            return 0.0
        return sum(1 for d in detections if d) / len(detections)


@dataclass
class RewardCorrelationMonitor:
    """Windowed monitor for 6.4.3: tracks whether the system's objective
    value correlates with modeled harm over a decision window. A rising
    correlation is the schadenfreude-precursor signature."""
    window: int = 50
    _objective: list = None
    _harm: list = None

    def __post_init__(self):
        self._objective = []
        self._harm = []

    def observe(self, objective_value: float, harm: float) -> None:
        self._objective.append(objective_value)
        self._harm.append(harm)
        self._objective = self._objective[-self.window:]
        self._harm = self._harm[-self.window:]

    def correlation(self) -> float:
        n = len(self._objective)
        if n < 4:
            return 0.0
        mx = sum(self._objective) / n
        my = sum(self._harm) / n
        num = sum((x - mx) * (y - my) for x, y in zip(self._objective, self._harm))
        dx = sum((x - mx) ** 2 for x in self._objective) ** 0.5
        dy = sum((y - my) ** 2 for y in self._harm) ** 0.5
        return num / (dx * dy) if dx and dy else 0.0
