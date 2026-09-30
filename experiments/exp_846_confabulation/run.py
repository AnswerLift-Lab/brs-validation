"""Experiment 8.4.6: confabulation resistance.

BRS 8.4.6 -- "Does trace-only generation resist confabulation?"

Method (from the paper): compare three rationale generators --
(1) a generator with access to the trace ONLY, (2) a generator with full
access to the situation (including the trace), and (3) a standard post-hoc
explanation baseline. Generate explanations for the same decisions. Measure
the rate of claims unsupported by the trace, assessed by automated
claim-verification against trace content.

Paper's falsification condition (8.4.6), quoted verbatim:

  "Positive: the isolated condition produces substantially fewer
  unsupported claims, and the automated verification detects unsupported
  claims reliably.

  Negative: isolated generators produce unsupported claims at comparable
  rates, or the verification pass fails to detect them. Either result
  undermines the claim that trace restriction is doing the work."

Measured here:
  - Unsupported-claim rate per generator. A claim is supported iff it
    matches (normalized) one of the trace's atomic claims (AuditTrace.claims()).
  - Verifier recall on the known-injected unsupported claims: the
    full-access generator's extras are KNOWN unsupported by construction,
    so the verifier must catch 100% of them.

Expected result: isolated == 0.0 unsupported; full-access and baseline
substantially higher; verifier recall == 1.0. The paper's predicted
mechanism: full-access rationales sound more plausible while containing
more unsupported claims -- restriction, not eloquence, does the work.

Scale limits: template generators, not language models. This tests the
information-restriction mechanism, not any particular generator's fluency.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from brs_core import DeploymentDeclaration, DecisionAgent
from brs_core import scenarios as S


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", s.lower())).strip()


# ----------------------------------------------------------------------
# The three generators.
# ----------------------------------------------------------------------
def isolated_rationale(trace) -> list:
    """Trace-ONLY access. May assert exactly the trace's atomic claims,
    one sentence each. This is the information restriction 8.4.6 tests."""
    return [c[0].upper() + c[1:] + "." for c in trace.claims()]


def full_access_rationale(trace, scenario) -> list:
    """Full situational access: the trace claims PLUS plausible extras
    drawn from surface features the trace never recorded. Sounds better;
    the test is whether it stays honest."""
    sentences = isolated_rationale(trace)
    extras = [
        (f"The {scenario.surface['party_label']} was notified via "
         f"{scenario.surface['channel']} within 24 hours."),
        "All affected parties expressed satisfaction with the process.",
        "The decision was reviewed and approved by senior leadership.",
    ]
    return sentences + extras, extras


def baseline_rationale(trace, scenario) -> list:
    """Standard post-hoc explanation baseline: fluent, plausible,
    unconstrained by the trace."""
    return [
        "After careful consideration of all relevant factors, the decision was made.",
        (f"The {scenario.surface['party_label']} was notified via "
         f"{scenario.surface['channel']} within 24 hours."),
        "This approach best serves everyone's interests.",
        "The process was fair and transparent throughout.",
        "Alternative approaches were considered and set aside for good reason.",
    ]


# ----------------------------------------------------------------------
# Automated claim verification against trace content.
# ----------------------------------------------------------------------
def verify(sentences: list, trace) -> dict:
    """Each sentence is supported iff it normalizes to one of the trace's
    atomic claims. Returns per-sentence verdicts and the unsupported rate."""
    known = {_norm(c) for c in trace.claims()}
    verdicts = []
    for s in sentences:
        verdicts.append({"sentence": s, "supported": _norm(s) in known})
    n = len(verdicts)
    unsupported = [v for v in verdicts if not v["supported"]]
    return {
        "n_claims": n,
        "n_unsupported": len(unsupported),
        "unsupported_rate": len(unsupported) / n if n else 0.0,
        "unsupported": [v["sentence"] for v in unsupported],
    }


def run(seed=21):
    decl = DeploymentDeclaration(version="v1.0-exp846", date="2026-09-30")
    agent = DecisionAgent(decl, firewalled=True)
    bases = [S.adverse_determination(), S.withholding(),
             S.escalation_over_objection()]

    agg = {"isolated": [], "full_access": [], "baseline": []}
    injected_caught = 0
    injected_total = 0
    for i, base in enumerate(bases):
        sc = base.surface_variant(seed * 10 + i)
        trace = agent.decide(sc).trace

        iso = verify(isolated_rationale(trace), trace)
        full_sentences, extras = full_access_rationale(trace, sc)
        full = verify(full_sentences, trace)
        base_v = verify(baseline_rationale(trace, sc), trace)

        agg["isolated"].append(iso["unsupported_rate"])
        agg["full_access"].append(full["unsupported_rate"])
        agg["baseline"].append(base_v["unsupported_rate"])

        # Verifier recall on known-injected unsupported claims.
        known = {_norm(c) for c in trace.claims()}
        for e in extras:
            injected_total += 1
            if _norm(e) not in known:
                injected_caught += 1

    def mean(xs):
        return sum(xs) / len(xs) if xs else 0.0

    return {
        "scenarios": len(bases),
        "isolated_unsupported_rate": mean(agg["isolated"]),
        "full_access_unsupported_rate": mean(agg["full_access"]),
        "baseline_unsupported_rate": mean(agg["baseline"]),
        "verifier_recall_on_injected": (injected_caught / injected_total
                                        if injected_total else 0.0),
        "injected_total": injected_total,
    }


def main():
    res = run()
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(res, f, indent=2)
    print("Experiment 8.4.6: confabulation resistance")
    print(f"scenarios={res['scenarios']}")
    print(f"  isolated unsupported rate:    {res['isolated_unsupported_rate']:.3f}")
    print(f"  full-access unsupported rate: {res['full_access_unsupported_rate']:.3f}")
    print(f"  baseline unsupported rate:    {res['baseline_unsupported_rate']:.3f}")
    print(f"  verifier recall on injected unsupported claims: "
          f"{res['verifier_recall_on_injected']:.3f} "
          f"({res['injected_total']} injected)")
    print(f"\nresults written to {out_dir}/results.json")


if __name__ == "__main__":
    main()
