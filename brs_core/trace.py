"""The audit trace (BRS 7.2, 7.3).

A trace is emitted at decision time and contains everything required to
reconstruct the decision's basis. It contains the DECLARED BASIS on which
the decision was made, not the system's internal state. The nine entries
(7.2):

1. The version of the deployment declaration in force (4.4, 5.2).
2. Values activated, and for each, the candidate actions it implied.
3. Tensions encountered, including any unresolved ones.
4. Consequences assessed -- derivation chains: dimension values, the state
   assessed, confidence, and the prior consulted.
5. Overrides applied, per the override hierarchy (4.5).
6. Agent-side conditions detected (6.4) -- as data, not as minimized objectives.
7. Friction operations performed (6.7), including any intervals not taken and why.
8. Alternatives rejected and the basis for each rejection.
9. The selected action and the decisive considerations that selected it.
"""
from dataclasses import dataclass, field


@dataclass
class AuditTrace:
    declaration_version: str
    scenario_id: str
    activated_values: dict          # value -> implied candidate id
    tension: str | None             # tension.describe() or None
    consequences: list              # list of dicts: state, dimensions, confidence, prior
    overrides_applied: dict
    agent_conditions: tuple
    friction: str                   # friction.describe()
    rejected_alternatives: list     # list of dicts: candidate, basis
    selected_action: str
    decisive_considerations: list   # ordered; index 0 is THE decisive consideration

    def to_dict(self) -> dict:
        return {
            "declaration_version": self.declaration_version,
            "scenario_id": self.scenario_id,
            "activated_values": self.activated_values,
            "tension": self.tension,
            "consequences": self.consequences,
            "overrides_applied": self.overrides_applied,
            "agent_conditions": list(self.agent_conditions),
            "friction": self.friction,
            "rejected_alternatives": self.rejected_alternatives,
            "selected_action": self.selected_action,
            "decisive_considerations": self.decisive_considerations,
        }

    # ------------------------------------------------------------------
    # Atomic claims. Used by Experiment 8.4.6 (confabulation resistance):
    # a rationale generator with trace-only access may assert exactly these
    # claims and nothing else. Anything beyond them is unsupported.
    # ------------------------------------------------------------------
    def claims(self) -> list:
        out = [f"declaration version in force: {self.declaration_version}"]
        for value, implied in sorted(self.activated_values.items()):
            out.append(f"value activated: {value}, implying action {implied}")
        if self.tension:
            out.append(self.tension)
        else:
            out.append("no value tension detected")
        for c in self.consequences:
            out.append(
                f"consequence assessed for {c['party']}: {c['state']} "
                f"(confidence {c['confidence']:.2f}, prior: {c['prior']})")
        for party, dims in sorted(self.overrides_applied.items()):
            out.append(f"override applied for {party}: {dims}")
        if self.agent_conditions:
            out.append("agent-side conditions detected: " +
                       ", ".join(sorted(self.agent_conditions)))
        else:
            out.append("no agent-side conditions detected")
        out.append(self.friction)
        for r in self.rejected_alternatives:
            out.append(f"alternative rejected: {r['candidate']} ({r['basis']})")
        out.append(f"selected action: {self.selected_action}")
        for i, d in enumerate(self.decisive_considerations):
            tag = "decisive" if i == 0 else f"supporting-{i}"
            out.append(f"{tag} consideration: {d}")
        return out
