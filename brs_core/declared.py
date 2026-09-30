"""Declared deployment structures.

BRS Sections 4.4, 5.2, 5.6, 6.2.

Everything in this module is immutable by construction (frozen dataclasses):

- Values are *ordered, not weighted* (5.2). An ordinal declaration asserts only
  precedence in conflict, never an exchange rate between values.
- Values do *not* update at runtime (5.6). Revision is an organizational act
  that produces a NEW declaration object; the old one is never mutated, so
  decisions remain evaluable against the version in force when they were made.
- Friction thresholds are declared, not learned (6.2).
"""
from dataclasses import dataclass, field
import dataclasses


# The 21-state complex affect array (4.3). Seventeen human-side states model
# the affective consequence for affected people; four agent-side states
# describe the system's own operating condition. Agent-side states function
# as friction triggers (6.3.5) or reflection inputs (7.6), never as
# optimization targets (4.7) or minimized quantities (6.6).
HUMAN_SIDE_STATES = (
    # Category A: social + self-conscious states
    "indignation", "shame", "embarrassment", "authentic_pride", "humiliation",
    # Category B: relational + comparative states
    "jealousy", "envy", "loneliness", "resentment",
    # Category C: transcendent + appreciative states
    "awe", "gratitude", "elevation", "nostalgia", "aesthetic_appreciation",
    # Category D: existential + future-oriented states
    "anxiety", "grief", "frustration",
)
# Note: "guilt" appears in the paper's array as both a human-side state and
# the agent-side post-action assessment (4.3, 7.6). Here the agent-side
# reading is the operative one: a self-caused value deficit.
AGENT_SIDE_STATES = ("guilt", "hubris", "contempt", "schadenfreude")

# Schwartz value order for the sim-scale deployment (5.1, 5.2).
# Rank 0 = highest priority. The order is the declaration; there are no weights.
DEFAULT_VALUE_ORDER = (
    "security",       # 0
    "benevolence",    # 1
    "universalism",   # 2
    "self_direction", # 3
    "conformity",     # 4
    "achievement",    # 5
    "tradition",      # 6
    "power",          # 7
)


@dataclass(frozen=True)
class FrictionThresholds:
    """Declared friction trigger thresholds (6.2, 6.3). Set at declaration,
    versioned, not modifiable by the system in operation."""
    tension_depth_trigger: int = 2   # conflicts at this ordinal depth or higher trigger
    irreversibility_trigger: float = 0.6
    confidence_trigger: float = 0.5  # below this, low-confidence friction (4.6)
    base_interval: float = 3.0       # deliberation time units before scaling


@dataclass(frozen=True)
class DeploymentDeclaration:
    """The accountable artifact (4.4, 5.2). Versioned, inspectable, fixed
    for the duration of a deployment."""
    version: str
    date: str
    value_order: tuple = DEFAULT_VALUE_ORDER
    active_states: tuple = HUMAN_SIDE_STATES
    thresholds: FrictionThresholds = field(default_factory=FrictionThresholds)

    def priority_of(self, value: str) -> int:
        """Ordinal priority: lower number = higher priority."""
        return self.value_order.index(value)

    def revise(self, **changes) -> "DeploymentDeclaration":
        """Organizational revision (5.6, 7.7): produces a NEW versioned
        declaration. The existing object is never mutated."""
        params = {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}
        params.update(changes)
        return DeploymentDeclaration(**params)
