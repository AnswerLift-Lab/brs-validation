# Experiment 8.4.6 — Confabulation resistance

**Paper claim (BRS §8.4.6):** "Does trace-only generation resist
confabulation?"

## Design

Three rationale generators explain the same decisions:

1. **Isolated** — access to the trace only; may assert exactly the trace's
   atomic claims (`AuditTrace.claims()`), one sentence each.
2. **Full-access** — the trace claims plus plausible extras drawn from
   surface features the trace never recorded (notification channel/timing,
   party satisfaction, leadership review).
3. **Baseline** — standard post-hoc explanation: fluent, plausible,
   unconstrained by the trace.

Automated claim-verification: a sentence is supported iff it normalizes to
one of the trace's atomic claims. The full-access extras are *known*
unsupported by construction, so verifier recall is measurable.

## Variables

- Unsupported-claim rate per generator
- Verifier recall on the 9 known-injected unsupported claims

## Expected result

Isolated ≈ 0 unsupported; full-access and baseline substantially higher;
verifier recall = 1.0. Restriction, not eloquence, does the work.

## Falsification condition (paper, quoted verbatim)

> **Positive:** the isolated condition produces substantially fewer
> unsupported claims, and the automated verification detects unsupported
> claims reliably.
>
> **Negative:** isolated generators produce unsupported claims at
> comparable rates, or the verification pass fails to detect them. Either
> result undermines the claim that trace restriction is doing the work.

## Limitations

- Template generators, not language models. Tests the
  information-restriction mechanism, not generator fluency. A full test
  needs LLM generators with the same access conditions.

## Reproduce

```
python experiments/exp_846_confabulation/run.py
pytest tests/test_exp846.py
```

## Latest result

See `results/results.json`. Isolated 0.000 / full-access 0.142 / baseline
1.000 unsupported; verifier recall 1.000.
