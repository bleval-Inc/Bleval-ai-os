"""Engine package — core platform capabilities.

Each engine provides a system-level capability that agents and workflows
consume.  Engines are modular — they can be swapped independently.
"""

from axiom.engine.memory import MemoryEngine
from axiom.engine.event import EventEngine
from axiom.engine.tool import ToolEngine
from axiom.engine.workflow import WorkflowEngine
from axiom.engine.executive import ExecutiveEngine
from axiom.engine.intelligence import IntelligenceEngine
from axiom.engine.learning import (
    LearningEngine,
    ScoreTracker,
    PatternDetector,
    RecommendationEngine,
    KnowledgeConsolidator,
)

__all__ = [
    "MemoryEngine",
    "EventEngine",
    "ToolEngine",
    "WorkflowEngine",
    "ExecutiveEngine",
    "IntelligenceEngine",
    "LearningEngine",
    "ScoreTracker",
    "PatternDetector",
    "RecommendationEngine",
    "KnowledgeConsolidator",
]