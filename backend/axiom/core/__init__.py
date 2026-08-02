"""AXIOM Core — top-level AI concierge for the AXIOM AI OS.

AXIOM sits above the executives (Jenson, Valta Prime, Yamako) and acts as
the Founder's primary interface — a JARVIS-like intelligence layer that
provides system awareness, conversational intelligence, research workspace
management, request routing, and self-healing coordination.

Sub-modules:
  - axiom_core         : The main AXIOMCore class (boot, chat, awareness)
  - request_router     : Natural-language request classification and routing
  - system_health      : Health state model + continuous monitoring
  - self_healer        : Autonomous failure detection and recovery
  - research_workspace : Research workspace lifecycle manager
"""

from axiom.core.axiom_core import AXIOMCore, AxiomBootResult, SystemAwareness, SystemState, BootStage
from axiom.core.request_router import RequestRouter, RequestCategory, ClassifiedRequest, RoutedAction
from axiom.core.research_workspace import ResearchWorkspaceManager, ResearchWorkspace

__all__ = [
    "AXIOMCore",
    "AxiomBootResult",
    "SystemAwareness",
    "SystemState",
    "BootStage",
    "RequestRouter",
    "RequestCategory",
    "ClassifiedRequest",
    "RoutedAction",
    "ResearchWorkspaceManager",
    "ResearchWorkspace",
]