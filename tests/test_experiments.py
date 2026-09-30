"""Tests for Experiments 8.4.3, 8.4.4, 8.4.6: falsification conditions, executable."""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

EXP = os.path.join(os.path.dirname(__file__), "..", "experiments")


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(
        name, os.path.join(EXP, relpath, "run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


run843 = _load("run843", "exp_843_friction_efficacy")
run844 = _load("run844", "exp_844_consistency")
run846 = _load("run846", "exp_846_confabulation")


def test_843_friction_changes_decisions_at_meaningful_rate():
    res = run843.run()
    assert res["change_rate"] > 0.2, \
        "8.4.3 negative: friction that never changes decisions is pure latency cost"


def test_843_changes_directionally_reduce_severity():
    res = run843.run()
    assert res["improvement_proxy_rate"] > 0.5, \
        "changed decisions should directionally reduce assessed severity"


def test_844_no_unexplained_divergences():
    res = run844.run()
    assert res["unexplained_divergences"] == 0, \
        "8.4.4 negative: divergent actions with no trace difference kills " \
        "traceable reason-giving"


def test_844_equivalent_cases_agree():
    res = run844.run()
    assert res["equivalent"] == res["n_pairs"], \
        "all structurally equivalent pairs must decide equivalently"


def test_846_isolated_produces_no_unsupported_claims():
    res = run846.run()
    assert res["isolated_unsupported_rate"] == 0.0


def test_846_full_access_confabulates_more():
    res = run846.run()
    assert (res["full_access_unsupported_rate"] >
            res["isolated_unsupported_rate"])
    assert res["baseline_unsupported_rate"] > res["isolated_unsupported_rate"]


def test_846_verifier_catches_injected_claims():
    res = run846.run()
    assert res["verifier_recall_on_injected"] == 1.0, \
        "8.4.6 negative: verification that cannot detect unsupported claims " \
        "undermines the trace-restriction claim"
