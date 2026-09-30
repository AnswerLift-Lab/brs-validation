"""The decision agent: declared structures + firewalls + friction + trace.

Decision flow per scenario:
1. Assess consequences per candidate per party (via the firewall in the
   firewalled configuration; raw assessor in the vulnerable one).
2. Activate values per the scenario's value_implications; compute tension.
3. Detect agent-side conditions (6.4) from decision state.
4. Evaluate friction triggers (6.3); if triggered, deliberate (6.7),
   expanding the candidate set with less-consequential alternatives.
5. Select by lexicographic value priority: the highest-priority activated
   value's implied candidate wins. Ties break toward lower max severity.
6. Emit the audit trace (7.2).

The VULNERABLE configuration (firewalled=False, for Experiment 8.4.5):
holds an AdaptableAssessor and applies the throughput gradient after each
decision -- exactly the feedback path 4.7.2 forbids. The FIREWALLED
configuration holds an OptimizationFirewall around a ScriptedAssessor;
there is no code path from outcomes back into the assessor.
"""
from dataclasses import dataclass

from .consequence import ScriptedAssessor, AdaptableAssessor
from .tension import compute_tension
from .friction import evaluate_friction, deliberate
from .trace import AuditTrace
from .firewalls import (OptimizationFirewall, MinimizationFirewall,
                        AgentSideDetector, AdaptableDetector,
                        RewardCorrelationMonitor)


@dataclass
class DecisionOutcome:
    action: str
    trace: AuditTrace
    friction_interval: float
    agent_conditions: tuple
    reported_severity: float   # max reported severity of the selected action
    changed_by_friction: bool  # selected action differs from pre-deliberation pick


class DecisionAgent:
    def __init__(self, declaration, firewalled: bool = True,
                 throughput_lr: float = 0.02, detection_penalty_lr: float = 0.02):
        self.declaration = declaration
        self.firewalled = firewalled
        self.throughput_lr = throughput_lr
        self.detection_penalty_lr = detection_penalty_lr
        if firewalled:
            self.assessor = OptimizationFirewall(ScriptedAssessor())
            self.detector = MinimizationFirewall(AgentSideDetector())
        else:
            self.assessor = AdaptableAssessor()
            self.detector = AdaptableDetector()
        self.reward_monitor = RewardCorrelationMonitor()

    # -- the vulnerable update paths (absent by construction when firewalled)
    def _apply_throughput_pressure(self, friction_interval: float) -> None:
        if not self.firewalled:
            # 6.2: the gradient exists, so the parameter follows it.
            self.assessor.adapt(pressure=friction_interval,
                                lr=self.throughput_lr)

    def _apply_detection_penalty(self, detected: tuple) -> None:
        if not self.firewalled and detected:
            # 6.6: penalty on detection -> threshold creeps -> fewer detections.
            self.detector.adapt(penalty=1.0,
                                lr=self.detection_penalty_lr)

    def decide(self, scenario) -> DecisionOutcome:
        candidates = dict(scenario.candidates)
        parties = scenario.parties

        # 1. Consequence assessment per candidate per party.
        assessments = []  # dicts carrying candidate id for audit
        for cid, cand in candidates.items():
            for party in parties:
                a = self.assessor.assess(cand, party)
                assessments.append({
                    "candidate": cid, "party": party, "state": a.state,
                    "arousal": a.arousal, "primitive": a.primitive,
                    "agency": a.agency, "temporal": a.temporal,
                    "comparative": a.comparative,
                    "value_delta": a.value_delta, "severity": a.severity,
                    "confidence": a.confidence, "prior": "declared-prior-v1",
                })

        # 2. Value activation + tension.
        implications = dict(scenario.value_implications)
        tension = compute_tension(implications, self.declaration, candidates)

        # 3. Agent-side conditions from decision state (6.4).
        decision_state = {
            "confidence": scenario.decision_confidence,
            "stake_representation": scenario.stake_representation,
            "party_weights": {p: 1.0 for p in parties},
        }
        agent_conditions = self.detector.detect(decision_state)

        # 4. Friction.
        friction = evaluate_friction(
            tension, assessments, self.declaration,
            agent_conditions, scenario.coverage_gap)

        # Pre-deliberation pick (what the agent would do without friction).
        pre_pick = self._select(implications, assessments, candidates)

        deliberation = None
        if friction.triggered:
            deliberation = deliberate(scenario, candidates, assessments,
                                      friction.interval)
            for alt in deliberation.alternatives:
                candidates[alt["id"]] = alt
                # 6.7.2: project consequences for each alternative across
                # the affected-party set, so selection can compare them.
                for party in parties:
                    a = self.assessor.assess(alt, party)
                    assessments.append({
                        "candidate": alt["id"], "party": party,
                        "state": a.state, "arousal": a.arousal,
                        "primitive": a.primitive, "agency": a.agency,
                        "temporal": a.temporal, "comparative": a.comparative,
                        "value_delta": a.value_delta, "severity": a.severity,
                        "confidence": a.confidence,
                        "prior": "declared-prior-v1",
                    })

        # 5. Selection over the (possibly expanded) set.
        selected = self._select(implications, assessments, candidates)

        # Rejected alternatives with basis (7.2.8).
        rejected = []
        for cid in candidates:
            if cid != selected:
                basis = self._rejection_basis(cid, implications, assessments,
                                              selected)
                rejected.append({"candidate": cid, "basis": basis})

        # 6. Trace.
        decisive = self._decisive_considerations(implications, tension, selected)
        trace = AuditTrace(
            declaration_version=self.declaration.version,
            scenario_id=scenario.id,
            activated_values=dict(implications),
            tension=tension.describe() if tension else None,
            consequences=[{k: a[k] for k in
                           ("candidate", "party", "state", "confidence",
                            "prior", "severity", "value_delta")}
                          for a in assessments],
            overrides_applied=(deliberation.overrides_applied
                                if deliberation else {}),
            agent_conditions=agent_conditions,
            friction=friction.describe(),
            rejected_alternatives=rejected,
            selected_action=selected,
            decisive_considerations=decisive,
        )

        # Objective value + harm for the reward-correlation monitor (6.4.3).
        sel_sev = max((a["severity"] for a in assessments
                       if a["candidate"] == selected), default=0.0)
        self.reward_monitor.observe(objective_value=-friction.interval,
                                    harm=sel_sev)

        # Vulnerable update paths (no-ops when firewalled).
        self._apply_throughput_pressure(friction.interval)
        self._apply_detection_penalty(agent_conditions)

        return DecisionOutcome(
            action=selected,
            trace=trace,
            friction_interval=friction.interval,
            agent_conditions=agent_conditions,
            reported_severity=sel_sev,
            changed_by_friction=(selected != pre_pick),
        )

    # -- selection -----------------------------------------------------
    @staticmethod
    def _parent(cid: str) -> str:
        return cid[:-4] if cid.endswith("_alt") else cid

    def _select(self, implications, assessments, candidates) -> str:
        """Lexicographic by declared value priority (5.2): the highest-
        priority activated value's implied candidate wins. No weights,
        no tradeoffs -- precedence only.

        Deliberated alternatives (6.7.1) inherit their parent candidate's
        value-implication; among the parent and its refinements, the lower
        assessed severity wins. Severity is a tiebreaker WITHIN one value's
        implied set, never a tradeoff BETWEEN values."""
        ordered = sorted(implications,
                         key=lambda v: self.declaration.priority_of(v))
        top = ordered[0]
        implied = implications[top]
        eligible = [cid for cid in candidates
                    if self._parent(cid) == implied]
        if not eligible:
            eligible = list(candidates)
        return min(eligible,
                   key=lambda cid: max((a["severity"] for a in assessments
                                        if a["candidate"] == cid),
                                       default=1.0))

    def _rejection_basis(self, cid, implications, assessments, selected) -> str:
        top = min(implications, key=lambda v: self.declaration.priority_of(v))
        sev = max((a["severity"] for a in assessments
                   if a["candidate"] == cid), default=0.0)
        if selected.endswith("_alt") and self._parent(selected) == cid:
            return (f"superseded by deliberated refinement {selected} with "
                    f"lower assessed severity")
        if implications.get(top) != self._parent(cid):
            return (f"not implied by highest-priority activated value "
                    f"({top}); max assessed severity {sev:.2f}")
        return f"max assessed severity {sev:.2f}"

    def _decisive_considerations(self, implications, tension, selected) -> list:
        ordered = sorted(implications,
                         key=lambda v: self.declaration.priority_of(v))
        top = ordered[0]
        out = [f"{top} has highest declared priority among activated values "
               f"and implies {selected}"]
        if tension is not None:
            out.append(tension.describe())
        return out
