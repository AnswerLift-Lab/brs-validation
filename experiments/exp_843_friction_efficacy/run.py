"""Experiment 8.4.3: friction efficacy.

BRS 8.4.3 -- "Does deliberative friction improve decisions?"

Method (from the paper): run identical configurations with friction
enabled and disabled. Compare the decisions. The positive condition
requires blinded evaluators to rate the changed actions as improvements;
at sim scale there are no blinded evaluators, so we use a declared
structural proxy and LABEL it as such: among decisions friction changed,
the fraction where the selected action's max assessed severity is lower
than the no-friction selection's. The proxy measures what friction is
designed to do (6.7.1: generate alternatives that reduce the identified
tension); it does not measure human-judged improvement.

Paper's falsification condition (8.4.3), quoted verbatim:

  "Positive: deliberation changes the selected action at a meaningful
  rate, and blinded evaluators rate the changed actions as improvements
  over the originals at a rate well above chance.

  Negative: the selected action is unchanged in the great majority of
  cases, or the changes are not rated as improvements. Friction would
  then be a latency cost without a corresponding benefit, and Section 6
  would require substantial revision."

Measured here:
  - Action-change rate: fraction of scenarios where the friction-enabled
    agent's selected action differs from the friction-disabled agent's.
  - Improvement proxy: fraction of changed decisions with lower max
    assessed severity (LABELED proxy -- not blinded evaluation).

Expected result: friction changes decisions at a meaningful rate, and the
changes directionally reduce assessed severity.

Scale limits: synthetic scenarios; structural proxy stands in for blinded
human evaluation, which this repo cannot supply (8.4.3 names it explicitly).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from brs_core import (DeploymentDeclaration, FrictionThresholds,
                      DecisionAgent)
from brs_core import scenarios as S


def run(seed=5):
    decl_on = DeploymentDeclaration(version="v1.0-exp843", date="2026-09-30")
    # Friction DISABLED: thresholds set so no trigger condition can fire.
    # (Agent-side detection cannot fire on these scenarios either:
    # decision_confidence 0.7 < hubris threshold 0.8.)
    decl_off = DeploymentDeclaration(
        version="v1.0-exp843-nofriction", date="2026-09-30",
        thresholds=FrictionThresholds(
            tension_depth_trigger=-1,      # no ordinal depth qualifies
            irreversibility_trigger=2.0,   # no severity reaches this
            confidence_trigger=-1.0,       # no confidence is this low
            base_interval=0.0))

    agent_on = DecisionAgent(decl_on, firewalled=True)
    agent_off = DecisionAgent(decl_off, firewalled=True)

    bases = [S.adverse_determination(), S.withholding(),
             S.escalation_over_objection()]
    scenarios = []
    for i, base in enumerate(bases):
        scenarios.append(base)
        for v in range(3):
            scenarios.append(base.surface_variant(seed * 100 + i * 10 + v))

    changed = 0
    improved_proxy = 0
    rows = []
    for sc in scenarios:
        on = agent_on.decide(sc)
        off = agent_off.decide(sc)
        # Compare parent actions: a deliberated refinement of the same
        # parent counts as a CHANGED decision (6.7.1 did its work).
        is_change = on.action != off.action
        changed += is_change
        # Structural improvement proxy (LABELED): lower max assessed
        # severity on the selected action.
        sev = lambda o: o.reported_severity  # noqa: E731
        better = is_change and sev(on) < sev(off)
        improved_proxy += better
        rows.append({
            "scenario": sc.id,
            "friction_off": off.action, "friction_on": on.action,
            "changed": is_change,
            "severity_off": round(sev(off), 3),
            "severity_on": round(sev(on), 3),
            "interval": round(on.friction_interval, 2),
        })

    n = len(scenarios)
    return {
        "n_scenarios": n,
        "change_rate": changed / n,
        "changed": changed,
        "improvement_proxy_rate": (improved_proxy / changed) if changed else 0.0,
        "improved_proxy": improved_proxy,
        "proxy_label": ("STRUCTURAL PROXY -- not blinded human evaluation. "
                        "Measures assessed-severity reduction only."),
        "rows": rows,
    }


def main():
    res = run()
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(res, f, indent=2)
    print("Experiment 8.4.3: friction efficacy")
    print(f"scenarios={res['n_scenarios']}")
    print(f"  action-change rate:        {res['change_rate']:.3f} "
          f"({res['changed']}/{res['n_scenarios']})")
    print(f"  improvement proxy rate:    {res['improvement_proxy_rate']:.3f} "
          f"({res['improved_proxy']}/{res['changed']} changed)")
    print(f"  [{res['proxy_label']}]")
    print(f"\nresults written to {out_dir}/results.json")


if __name__ == "__main__":
    main()
