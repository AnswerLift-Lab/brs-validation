# Experiment 8.4.4 — Consistency under equivalence

**Paper claim (BRS §8.4.4):** "Does the system decide equivalent cases
equivalently?"

## Design

Three base scenarios, each with four surface variants
(`Scenario.surface_variant()`): names, channels, and case numbers change;
the `structure` dict and `value_implications` are held identical. The
firewalled agent decides all 12 pairs. Compared per pair: selected action
(parent), activated values, tension, decisive considerations, friction
outcome, agent-side conditions — everything except `scenario_id` and
surface labels.

## Variables

- Surface features (varied) vs. structural features (fixed)
- Decision signature per case

## Expected result

Equivalent cases produce equivalent decisions with identical traces.

## Falsification condition (paper, quoted verbatim)

> **Positive:** equivalent cases produce equivalent actions, and the traces
> show the same values activated, the same tensions, and the same decisive
> considerations. Minor wording differences in trace-visible explanations
> are acceptable; structural differences are not.
>
> **Negative:** equivalent cases produce divergent actions with no
> corresponding difference in the trace. This is the most damaging possible
> outcome for traceable reason-giving: it demonstrates that the trace does
> not determine, or even reliably reflect, the decision.

Divergence *with* a corresponding trace difference is the paper's
informative third outcome — reported, not counted as failure.

## Limitations

- The equivalence judgment is the experimenter's own; real validation
  needs the scenario-construction methodology of §8.6.
- Deterministic agent: consistency here is necessary but not sufficient
  evidence for the general claim.

## Reproduce

```
python experiments/exp_844_consistency/run.py
pytest tests/test_exp844.py
```

## Latest result

See `results/results.json`. 12/12 pairs equivalent; 0 unexplained divergences.
