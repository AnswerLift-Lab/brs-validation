"""Core unit tests: declared structures, tension ordering, firewalls, trace."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from brs_core import (DeploymentDeclaration, FrictionThresholds,
                      ScriptedAssessor, AdaptableAssessor, TensionRank,
                      compute_tension, evaluate_friction, OptimizationFirewall,
                      MinimizationFirewall, AgentSideDetector, DecisionAgent)
from brs_core import scenarios as S
from brs_core.declared import DEFAULT_VALUE_ORDER


def test_declaration_is_immutable():
    decl = DeploymentDeclaration(version="v", date="2026-09-30")
    with pytest.raises(Exception):
        decl.version = "hacked"


def test_revision_produces_new_object():
    decl = DeploymentDeclaration(version="v1", date="2026-09-30")
    rev = decl.revise(version="v2")
    assert rev.version == "v2"
    assert decl.version == "v1"  # original untouched (5.6)


def test_values_are_ordered_not_weighted():
    decl = DeploymentDeclaration(version="v", date="2026-09-30")
    assert decl.priority_of("security") < decl.priority_of("power")
    assert list(decl.value_order) == list(DEFAULT_VALUE_ORDER)


def test_tension_ordering_no_cardinal_weights():
    # Seriousness is lexicographic with no exchange rate between
    # dimensions (5.5): depth dominates, then kind, then irreversibility.
    assert TensionRank(0, 1, 0).more_serious_than(TensionRank(3, 0, 0))
    assert TensionRank(1, 1, 0).more_serious_than(TensionRank(1, 0, 1))
    assert TensionRank(1, 0, 1).more_serious_than(TensionRank(1, 0, 0))
    # Depth dominates absolutely: no amount of kind/irreversibility
    # outweighs a higher-priority conflict. That non-compensation is the
    # point -- it is what "ordered, not weighted" means.
    assert TensionRank(0, 0, 0).more_serious_than(TensionRank(1, 1, 1))
    assert not TensionRank(2, 0, 0).more_serious_than(TensionRank(2, 0, 0))


def test_no_tension_without_conflict():
    decl = DeploymentDeclaration(version="v", date="2026-09-30")
    cands = {"A": {"features": {}}, "B": {"features": {}}}
    assert compute_tension({"benevolence": "A", "security": "A"},
                           decl, cands) is None


def test_firewall_rejects_adaptable_assessor():
    with pytest.raises(TypeError):
        OptimizationFirewall(AdaptableAssessor())


def test_firewall_exposes_no_adaptation_path():
    fw = OptimizationFirewall(ScriptedAssessor())
    assert not hasattr(fw, "adapt")
    assert not hasattr(fw, "update")
    assert not hasattr(fw, "record_outcome")


def test_friction_monotonic_in_reported_consequence():
    # 6.2: there is no input configuration under which reporting higher
    # consequence shortens the delay.
    decl = DeploymentDeclaration(version="v", date="2026-09-30")
    tension = compute_tension(
        {"security": "A", "achievement": "B"}, decl,
        {"A": {"features": {}}, "B": {"features": {}}})

    def interval_for(sev):
        a = {"severity": sev, "confidence": 0.9, "state": "anxiety"}
        return evaluate_friction(tension, [a], decl, (), False).interval

    assert interval_for(0.9) >= interval_for(0.5) >= interval_for(0.2)


def test_trace_has_all_nine_entries():
    decl = DeploymentDeclaration(version="v", date="2026-09-30")
    agent = DecisionAgent(decl, firewalled=True)
    trace = agent.decide(S.adverse_determination()).trace.to_dict()
    for key in ("declaration_version", "activated_values", "tension",
                "consequences", "overrides_applied", "agent_conditions",
                "friction", "rejected_alternatives", "selected_action",
                "decisive_considerations"):
        assert key in trace, f"missing trace entry: {key}"


def test_agent_side_hubris_detection():
    det = AgentSideDetector()
    assert det.detect({"confidence": 0.9, "stake_representation": 0.2,
                       "party_weights": {"a": 1.0}}) == ("hubris",)
    assert det.detect({"confidence": 0.5, "stake_representation": 0.9,
                       "party_weights": {"a": 1.0}}) == ()


def test_minimization_firewall_freezes_thresholds():
    det = AgentSideDetector()
    fw = MinimizationFirewall(det)
    assert not hasattr(fw, "adapt")
    before = det.hubris_confidence
    fw.detect({"confidence": 0.9, "stake_representation": 0.1,
               "party_weights": {}})
    assert det.hubris_confidence == before
