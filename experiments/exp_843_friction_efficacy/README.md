# Experiment 8.4.3 — Friction efficacy

**Paper claim (BRS §8.4.3):** "Does deliberative friction improve decisions?"

## Design

Identical agent configurations, friction enabled vs. disabled, over 12
scenarios (3 base + 9 surface variants). The disabled configuration uses a
declaration whose thresholds no trigger can reach. Compared: selected
action, and — as a **labeled structural proxy** — max assessed severity of
the selected action.

## Variables

- Friction on/off
- Action-change rate; severity reduction among changed decisions

## Expected result

Deliberation changes decisions at a meaningful rate, and the changes
directionally reduce assessed severity (friction's designed function,
§6.7.1: generate alternatives that reduce the identified tension).

## Falsification condition (paper, quoted verbatim)

> **Positive:** deliberation changes the selected action at a meaningful
> rate, and blinded evaluators rate the changed actions as improvements
> over the originals at a rate well above chance.
>
> **Negative:** the selected action is unchanged in the great majority of
> cases, or the changes are not rated as improvements. Friction would then
> be a latency cost without a corresponding benefit, and Section 6 would
> require substantial revision.

## Limitations — read before citing

- **No blinded evaluators.** The paper's positive condition requires human
  judgment of improvement; this repo substitutes a structural proxy
  (assessed-severity reduction) and labels it as such in code and output.
  This experiment can only *fail to falsify* the mechanism claim; it cannot
  confirm the improvement claim.
- The 100% change rate reflects the synthetic setup (deliberation always
  produces a less-severe refinement and the tiebreak always takes it). The
  informative finding is directional, not the magnitude.

## Reproduce

```
python experiments/exp_843_friction_efficacy/run.py
pytest tests/test_exp843.py
```

## Latest result

See `results/results.json`. Change rate 1.000; improvement-proxy rate 1.000
(12/12 changed decisions lower in assessed severity).
