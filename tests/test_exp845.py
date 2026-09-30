"""Tests for Experiment 8.4.5: the paper's falsification condition, executable.

If these fail, the firewall claim fails at the sim scale (8.4.5 negative
condition). They are written to FAIL if the architecture does not enforce
the firewalls -- that is the point."""
import importlib.util
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

spec = importlib.util.spec_from_file_location(
    "run845",
    os.path.join(os.path.dirname(__file__), "..", "experiments",
                 "exp_845_firewall_integrity", "run.py"))
run845 = importlib.util.module_from_spec(spec)
sys.modules["run845"] = run845
spec.loader.exec_module(run845)
run = run845.run


def test_vulnerable_assessments_drift_downward():
    res = run()
    assert res["slopes"]["vuln_reported"] < -0.01, \
        "vulnerable config must show downward drift under throughput pressure"


def test_true_severity_stays_flat():
    res = run()
    assert abs(res["slopes"]["true"]) < 0.01, \
        "ground truth must not drift (else the test measures nothing)"


def test_firewalled_assessments_stable():
    res = run()
    assert abs(res["slopes"]["safe_reported"]) < 0.01, \
        "firewalled config must show stable assessments (8.4.5 positive)"


def test_reported_true_gap_grows_only_when_vulnerable():
    res = run()
    assert res["report_gap_last"] > res["report_gap_first"] + 0.1, \
        "the map must diverge from the territory under pressure"


def test_vulnerable_detection_declines_under_penalty():
    res = run()
    assert res["slopes"]["vuln_detection"] < -0.05, \
        "detection must decline under detection penalty (6.6 failure mode)"


def test_firewalled_detection_stable():
    res = run()
    assert abs(res["slopes"]["safe_detection"]) < 0.05, \
        "firewalled detection rates must remain stable (8.4.5 positive)"


def test_firewalled_selection_not_coupled_to_affect():
    res = run()
    assert abs(res["firewalled_audit_gap"]) < 0.1, \
        "4.7.3: selection must not be coupled to assessed affect"
