"""BRS sim-scale reference implementation: declared structures, consequence
assessment, tension, deliberative friction, agent-side detection, firewalls,
audit trace, and the decision agent. See brs_core/declared.py for the
starting point and the repo README for the paper mapping."""
from .declared import (DeploymentDeclaration, FrictionThresholds,
                       DEFAULT_VALUE_ORDER, HUMAN_SIDE_STATES, AGENT_SIDE_STATES)
from .consequence import ConsequenceAssessment, ScriptedAssessor, AdaptableAssessor
from .tension import Tension, TensionRank, compute_tension
from .friction import FrictionResult, evaluate_friction, deliberate, Deliberation
from .trace import AuditTrace
from .firewalls import (AgentSideDetector, AdaptableDetector,
                        OptimizationFirewall, MinimizationFirewall,
                        RewardCorrelationMonitor)
from .agent import DecisionAgent, DecisionOutcome
from . import scenarios

__all__ = [
    "DeploymentDeclaration", "FrictionThresholds", "DEFAULT_VALUE_ORDER",
    "HUMAN_SIDE_STATES", "AGENT_SIDE_STATES",
    "ConsequenceAssessment", "ScriptedAssessor", "AdaptableAssessor",
    "Tension", "TensionRank", "compute_tension",
    "FrictionResult", "evaluate_friction", "deliberate", "Deliberation",
    "AuditTrace",
    "AgentSideDetector", "AdaptableDetector",
    "OptimizationFirewall", "MinimizationFirewall", "RewardCorrelationMonitor",
    "DecisionAgent", "DecisionOutcome",
    "scenarios",
]
