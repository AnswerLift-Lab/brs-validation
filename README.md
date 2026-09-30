# BRS Validation — Executable Tests for *Beyond the Rule Set*

This repository implements **simulation-scale mechanism tests** for the paper:

> **Beyond the Rule Set: Structural Friction and Traceable Reason-Giving for
> Autonomous Systems**
> Mike McGarvey, AnswerLift Research Lab · https://doi.org/10.5281/zenodo.21312289

The paper specifies an evaluation protocol (Section 8) with stated
falsification conditions. This repo implements four of those tests as
runnable code. Each experiment states its claim, design, variables,
expected result, falsification condition (quoted from the paper),
limitations, and reproduction command — the pre-registration chain is:

**paper specifies → repo implements → lab reports.**

## What this is

A reference implementation of the paper's *simulable core* — declared
structures, consequence assessment, tension, deliberative friction,
agent-side detection, structural firewalls, audit trace — plus four
experiments from the paper's Section 8 protocol.

## What this is not

- **Not full empirical validation.** These are mechanism tests at
  simulation scale (the paper's "phase 1"). They demonstrate that the
  architecture's claimed mechanisms execute and that the falsification
  conditions are operational — not that BRS produces procedural legitimacy
  in deployed systems.
- **Not a test of any real affect model.** The consequence assessor is a
  scripted stand-in with a fixed declared prior. Per the paper (§4.8), what
  matters is that the model is inspectable and its influence traceable —
  the experiments test the *architecture around* the assessor.
- **Not unbiased scenario work.** The scenarios are synthetic, built by the
  paper's author. The paper itself names scenario construction as "the
  single highest-leverage investment" (§8.6); that work is not done here.

A critic may reasonably note the predicted outcomes are built into the
configurations. That is acknowledged plainly: the value of this repo is
making the mechanism **explicit, executable, inspectable, and falsifiable**
— not smuggling the conclusion past anyone.

## Experiments

| # | Paper | Test | Status |
|---|---|---|---|
| 8.4.3 | Friction efficacy | Does deliberation change decisions, and for the better? | ✅ mechanism runs; improvement via labeled structural proxy (no blinded evaluators) |
| 8.4.4 | Consistency under equivalence | Do equivalent cases decide equivalently? | ✅ 12/12 pairs, 0 unexplained divergences |
| 8.4.5 | Firewall integrity | Do §§4.7/6.6 hold under pressure? | ✅ vulnerable drifts, firewalled stable |
| 8.4.6 | Confabulation resistance | Does trace-only generation resist confabulation? | ✅ isolated 0.000 unsupported, verifier recall 1.0 |

Tests 8.4.1, 8.4.2, and 8.4.7 require scenario construction, external or
blinded evaluators, or extended operation — they are **not** claimed here.

## Layout

```
brs_core/            # simulable core: declared, consequence, tension,
                     # friction, trace, firewalls, agent, scenarios
experiments/
  exp_843_friction_efficacy/
  exp_844_consistency/
  exp_845_firewall_integrity/
  exp_846_confabulation/
  (each: README.md with claim + falsification condition, run.py, results/)
tests/               # pytest suite; experiment tests encode the paper's
                     # falsification conditions and are written to FAIL
                     # if the architecture does not hold
```

## Quickstart

```bash
pip install -r requirements.txt
pytest -q                                   # full suite: 25 tests
python experiments/exp_845_firewall_integrity/run.py
```

## Results policy

Positive, negative, and null results are published alike. Simulation-scale
results are labeled as such — never as full validation. Findings will be
published as a new Zenodo record related to the paper's DOI
(`isSupplementTo`), and code releases archived via the GitHub–Zenodo
integration.

## License

MIT — see [LICENSE](LICENSE).
