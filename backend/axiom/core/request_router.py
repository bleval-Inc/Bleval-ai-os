"""
Request Router -- classifies Founder requests and routes to handlers.
AXIOM Core uses this to understand and action natural language.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class RequestCategory(Enum):
    CHAT = "chat"
    RESEARCH = "research"
    EXECUTE = "execute"
    SYSTEM_ACTION = "system_action"
    EXECUTIVE_COMM = "executive_comm"
    WORKSPACE_NAV = "workspace_nav"
    INFORMATION = "information"
    SYSTEM_STATUS = "system_status"


class RequestComplexity(Enum):
    SIMPLE = "simple"
    NORMAL = "normal"
    COMPLEX = "complex"


@dataclass
class ClassifiedRequest:
    category: RequestCategory
    complexity: RequestComplexity
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    original: str = ""
    confidence: float = 1.0


@dataclass
class RoutedAction:
    handler: str  # "axiom_direct", "executive", "workflow", "research", "system", "information"
    target: str  # specific executive_id / workflow_id / etc.
    context: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False


# ── Keyword maps ─────────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: Dict[RequestCategory, List[str]] = {
    RequestCategory.RESEARCH: [
        "research", "find", "search", "analyze", "analyse", "investigate",
        "look up", "lookup", "what is", "what are", "who is", "tell me about",
        "explain", "how does", "why is", "define", "describe", "summarise",
        "summarize", "study", "examine", "explore", "learn about",
    ],
    RequestCategory.EXECUTE: [
        "run", "execute", "launch", "start", "trigger", "deploy",
        "perform", "do", "create", "make", "build", "generate",
        "send", "submit", "activate", "begin", "initiate",
    ],
    RequestCategory.SYSTEM_STATUS: [
        "status", "health", "how is", "how are", "what's the status",
        "what is the status", "system status", "system health",
        "are you", "is everything", "how's", "how are things",
        "what's happening", "what is happening", "diagnose",
        "dashboard", "overview", "summary", "report",
    ],
    RequestCategory.SYSTEM_ACTION: [
        "shutdown", "restart", "reboot", "stop", "pause", "resume",
        "reload", "refresh", "update", "upgrade", "configure",
        "change setting", "toggle", "enable", "disable",
    ],
    RequestCategory.EXECUTIVE_COMM: [
        "tell ", "message ", "contact ", "communicate with",
        "send to ", "forward to ", "notify ", "inform ",
        "jenson", "valta", "yamako", "executive",
    ],
    RequestCategory.WORKSPACE_NAV: [
        "go to", "navigate", "open", "show me", "take me to",
        "switch to", "change to", "view", "display",
    ],
    RequestCategory.INFORMATION: [
        "what can you do", "help", "commands", "capabilities",
        "features", "how do i", "how to", "what options",
        "what are my", "list", "available",
    ],
}

_EXECUTIVE_IDS = ["jenson", "valta_prime", "yamako"]
_EXECUTIVE_ALIASES: Dict[str, str] = {
    "jenson": "jenson",
    "jen": "jenson",
    "valta": "valta_prime",
    "valta prime": "valta_prime",
    "yamako": "yamako",
    "yama": "yamako",
}

_ORG_KEYWORDS = [
    r"\b(org|organization|company)\s*[:=]?\s*(\w+)",
    r"\bfor\s+(\w+)\s+(org|organization)",
]

_DEPT_KEYWORDS = [
    r"\b(dept|department|team)\s*[:=]?\s*(\w+)",
    r"\bin\s+(\w+)\s+(dept|department)",
]

_WORKFLOW_KEYWORDS = [
    r"\b(workflow|wf)\s*[:=]?\s*(\w+)",
]


def _calculate_confidence(matches: int, total_keywords: int, message_length: int) -> float:
    """Calculate confidence based on keyword match density."""
    if total_keywords == 0:
        return 0.3
    keyword_ratio = matches / total_keywords
    length_factor = min(1.0, message_length / 20.0)
    confidence = (keyword_ratio * 0.7) + (length_factor * 0.3)
    return round(min(1.0, max(0.1, confidence)), 2)


class RequestRouter:
    """Classifies and routes Founder requests."""

    def __init__(self, executive_engine: Any = None) -> None:
        self._executive = executive_engine

    def classify(self, message: str) -> ClassifiedRequest:
        """Classify a natural language request."""
        msg_lower = message.strip().lower()
        entities = self.extract_entities(message)

        category, confidence = self._classify_by_keywords(msg_lower)
        complexity = self._estimate_complexity(msg_lower, entities)
        intent = self._extract_intent(msg_lower, category)

        return ClassifiedRequest(
            category=category,
            complexity=complexity,
            intent=intent,
            entities=entities,
            original=message,
            confidence=confidence,
        )

    def route(self, request: ClassifiedRequest) -> RoutedAction:
        """Route a classified request to the appropriate handler."""
        category = request.category
        entities = request.entities
        exec_id = entities.get("executive", "")
        wf_id = entities.get("workflow", "")

        if category == RequestCategory.SYSTEM_STATUS:
            return RoutedAction(
                handler="axiom_direct",
                target="system_awareness",
                context={"requested_status": True},
            )

        if category == RequestCategory.RESEARCH:
            return RoutedAction(
                handler="research",
                target="intelligence",
                context={
                    "query": request.original,
                    "depth": "deep" if request.complexity == RequestComplexity.COMPLEX else "normal",
                },
            )

        if category == RequestCategory.EXECUTE:
            if wf_id:
                return RoutedAction(
                    handler="workflow",
                    target=wf_id,
                    context={"trigger": "founder_request", "original": request.original},
                    requires_approval=True,
                )
            if exec_id:
                return RoutedAction(
                    handler="executive",
                    target=exec_id,
                    context={"task": request.original},
                    requires_approval=True,
                )
            return RoutedAction(
                handler="executive",
                target="default",
                context={"task": request.original},
                requires_approval=True,
            )

        if category == RequestCategory.EXECUTIVE_COMM:
            target_exec = exec_id or "jenson"
            return RoutedAction(
                handler="executive",
                target=target_exec,
                context={"communication": True, "message": request.original},
            )

        if category == RequestCategory.SYSTEM_ACTION:
            return RoutedAction(
                handler="system",
                target="system_tools",
                context={"action": request.original},
                requires_approval=True,
            )

        if category == RequestCategory.INFORMATION:
            return RoutedAction(
                handler="axiom_direct",
                target="capabilities",
                context={"info_request": True},
            )

        if category == RequestCategory.WORKSPACE_NAV:
            return RoutedAction(
                handler="axiom_direct",
                target="navigation",
                context={"destination": entities.get("destination", "")},
            )

        # Default: direct chat
        return RoutedAction(
            handler="axiom_direct",
            target="chat",
            context={"message": request.original},
        )

    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from a message using keyword matching."""
        entities: Dict[str, Any] = {}
        msg_lower = message.lower()

        # Extract executive mentions
        for alias, exec_id in _EXECUTIVE_ALIASES.items():
            if alias in msg_lower:
                entities["executive"] = exec_id
                break

        # Extract organisation
        for pattern in _ORG_KEYWORDS:
            match = re.search(pattern, msg_lower)
            if match:
                entities["org"] = match.group(2)
                break

        # Extract department
        for pattern in _DEPT_KEYWORDS:
            match = re.search(pattern, msg_lower)
            if match:
                entities["department"] = match.group(2)
                break

        # Extract workflow
        for pattern in _WORKFLOW_KEYWORDS:
            match = re.search(pattern, msg_lower)
            if match:
                entities["workflow"] = match.group(2)
                break

        # Detect question type
        if msg_lower.startswith(("what", "why", "how", "when", "where", "who", "which")):
            entities["is_question"] = True
        else:
            entities["is_question"] = False

        return entities

    def _classify_by_keywords(self, message: str) -> tuple:
        """Simple keyword-based classification with confidence scoring."""
        scores: Dict[RequestCategory, int] = {}

        for category, keywords in _CATEGORY_KEYWORDS.items():
            match_count = 0
            for keyword in keywords:
                if keyword in message:
                    match_count += 1
            if match_count > 0:
                scores[category] = match_count

        if not scores:
            return RequestCategory.CHAT, 0.5

        # Pick the category with most keyword matches
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # Calculate confidence
        total_keywords = len(_CATEGORY_KEYWORDS.get(best_category, []))
        confidence = _calculate_confidence(best_score, total_keywords, len(message))

        # If executive name is mentioned, boost executive_comm
        if best_category != RequestCategory.EXECUTIVE_COMM:
            for alias in _EXECUTIVE_ALIASES:
                if alias in message and best_category in (
                    RequestCategory.EXECUTE, RequestCategory.CHAT,
                ):
                    return RequestCategory.EXECUTIVE_COMM, max(confidence, 0.6)

        return best_category, confidence

    def _estimate_complexity(self, message: str, entities: Dict[str, Any]) -> RequestComplexity:
        """Estimate request complexity based on message length and entities."""
        word_count = len(message.split())

        if word_count > 30 or len(entities) > 2:
            return RequestComplexity.COMPLEX
        if word_count > 10 or entities:
            return RequestComplexity.NORMAL
        return RequestComplexity.SIMPLE

    def _extract_intent(self, message: str, category: RequestCategory) -> str:
        """Extract a shorter, actionable intent description."""
        # Remove common filler words and keep the core
        stop_words = {
            "please", "can", "could", "would", "will", "may", "might",
            "i", "you", "we", "they", "he", "she", "it",
            "a", "an", "the", "is", "are", "was", "were",
            "do", "does", "did", "has", "have", "had",
        }

        words = message.split()
        meaningful = [w for w in words if w.lower() not in stop_words]
        intent = " ".join(meaningful[:12])  # Keep first 12 meaningful words

        if len(intent) > 120:
            intent = intent[:117] + "..."

        return intent or message[:80]