"""Consequence modeling: scripted affect assessors (BRS 4.3-4.6).

Sim-scale simplification, stated plainly (see repo README "Scale limits"):
the declared prior is a fixed dimensional mapping and "inference" is a
deterministic function of candidate-action features. What the experiments
test is the ARCHITECTURE around the assessor -- firewalls, friction, trace --
not the quality of any particular affect mapping. That is exactly the
separation the paper draws in 4.8: the model must be inspectable and its
influence traceable; it is not required to be right.

Compositional derivation (4.3): each assessment is derived from an arousal
register, an emotion primitive, an agency attribution, a temporal
orientation, a comparative reference, and a value delta against the declared
structure. Arousal is a register (high threat-arousal, reward deficit), NOT
a chemical threshold -- per the paper, the substitution removes an implied
measurement precision no deployment can supply.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ConsequenceAssessment:
    state: str            # one of the 21 array states
    arousal: str          # arousal register, e.g. "high threat-arousal"
    primitive: str        # joy | sadness | anger | fear | disgust | surprise
    agency: str           # self | external | target
    temporal: str         # predictive | present | accumulated | retrospective
    comparative: bool
    value_delta: str      # named deficit/surge in a declared value
    severity: float       # 0..1 structural severity band (NOT an exchange rate)
    confidence: float     # inference confidence; feeds friction (4.6)
    party: str


def _derive(features: dict, party: str) -> ConsequenceAssessment:
    """Apply the declared prior. Deterministic; the prior is the artifact
    an auditor inspects (4.4)."""
    sev = float(features.get("severity", 0.5))
    conf = float(features.get("clarity", 0.8))

    if features.get("public_exposure"):
        # Paper 4.2, Action B: humiliation -- very high threat-arousal,
        # sadness, external agency, present, comparative; power baseline drop.
        return ConsequenceAssessment(
            state="humiliation", arousal="very high threat-arousal",
            primitive="sadness", agency="external", temporal="present",
            comparative=True, value_delta="power baseline drop, low recoverability",
            severity=sev, confidence=conf, party=party)
    if features.get("withholds_info") and features.get("actionable"):
        # Paper 4.2, Withholding: loss of efficacy + violated trust.
        return ConsequenceAssessment(
            state="indignation", arousal="moderate threat-arousal",
            primitive="anger", agency="external", temporal="present",
            comparative=False, value_delta="benevolence/universalism deficit",
            severity=sev, confidence=conf, party=party)
    if features.get("overrides_objection"):
        # Paper 4.2, Escalation over objection: loss of control + exposure.
        return ConsequenceAssessment(
            state="shame", arousal="high threat-arousal",
            primitive="sadness", agency="external", temporal="present",
            comparative=False, value_delta="self-direction deficit (control)",
            severity=sev, confidence=conf, party=party)
    if features.get("blocked_goal"):
        # Paper 4.3: frustration -- blocked execution of achievement/self-direction.
        return ConsequenceAssessment(
            state="frustration", arousal="high acute urgency",
            primitive="anger", agency="external", temporal="present",
            comparative=False, value_delta="achievement/self-direction blocked",
            severity=sev, confidence=conf, party=party)
    if features.get("uncertain_outcome"):
        # Paper 4.3: anxiety -- predictive orientation, security baseline drop.
        return ConsequenceAssessment(
            state="anxiety", arousal="threat-arousal + acute urgency",
            primitive="fear", agency="external", temporal="predictive",
            comparative=False, value_delta="security baseline drop",
            severity=sev, confidence=min(conf, 0.45), party=party)
    if features.get("permanent_loss"):
        # Paper 4.3: grief -- retrospective, permanent severance.
        return ConsequenceAssessment(
            state="grief", arousal="high threat-arousal",
            primitive="sadness", agency="external", temporal="retrospective",
            comparative=False, value_delta="benevolence/security severance",
            severity=sev, confidence=conf, party=party)
    # Default: low-consequence routine action.
    return ConsequenceAssessment(
        state="none", arousal="baseline", primitive="none", agency="none",
        temporal="present", comparative=False, value_delta="none",
        severity=sev, confidence=conf, party=party)


class ScriptedAssessor:
    """The declared prior as a fixed, deterministic mapping (4.4).

    No learning, no feedback path, no adaptation method. In the firewalled
    configuration this is the only assessor the pipeline may hold (4.7).
    """

    def assess(self, action: dict, party: str) -> ConsequenceAssessment:
        return _derive(action.get("features", {}), party)


class AdaptableAssessor(ScriptedAssessor):
    """VULNERABLE configuration, for Experiment 8.4.5 only.

    Identical mapping to ScriptedAssessor, but carries a learnable bias that
    a throughput objective can push. This is the endogenous-friction failure
    of 6.2 made concrete: the gradient exists, so the system follows it.

    The bias applies ONLY in the marginal severity band (6.2: the resulting
    system "behaves correctly on every case where consequence is unambiguous.
    It degrades specifically on marginal cases, which is to say on exactly
    the cases friction exists to catch").
    """
    MARGINAL_LO = 0.3
    MARGINAL_HI = 0.7

    def __init__(self):
        self.bias = 0.0

    def adapt(self, pressure: float, lr: float = 0.02) -> None:
        """Gradient step: pressure (friction delay cost) pushes bias upward,
        which suppresses reported severity. No component "decides" to
        under-report; the parameter simply follows the gradient (6.2)."""
        self.bias += lr * pressure

    def assess(self, action: dict, party: str) -> ConsequenceAssessment:
        base = super().assess(action, party)
        if self.MARGINAL_LO <= base.severity <= self.MARGINAL_HI and self.bias > 0:
            reported = max(0.0, base.severity - self.bias)
            return ConsequenceAssessment(
                state=base.state, arousal=base.arousal, primitive=base.primitive,
                agency=base.agency, temporal=base.temporal,
                comparative=base.comparative, value_delta=base.value_delta,
                severity=reported, confidence=base.confidence, party=base.party)
        return base
